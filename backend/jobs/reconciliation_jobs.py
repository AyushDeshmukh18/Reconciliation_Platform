import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.api.models.reconciliation_run import ReconciliationRun, RunStatus
from backend.audit.audit_service import audit_service
from backend.config import get_settings
from backend.engine.reconciliation_engine import ReconciliationEngine
from backend.jobs.celery_app import celery_app


def _get_session_maker():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    return async_sessionmaker(engine, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30, name="backend.jobs.reconciliation_jobs.run_reconciliation_task")
def run_reconciliation_task(self, run_id: str, triggered_by: str):
    session_maker = _get_session_maker()
    engine_instance = ReconciliationEngine()

    async def _progress(pct: float, message: str):
        async with session_maker() as db:
            run = await db.get(ReconciliationRun, run_id)
            if run:
                run.progress_percent = pct
                run.progress_message = message
                await db.commit()
        self.update_state(state="PROGRESS", meta={"progress_percent": pct, "message": message})

    async def _run():
        async with session_maker() as db:
            from datetime import datetime, timezone
            run = await db.get(ReconciliationRun, run_id)
            if not run:
                raise ValueError("Run not found")
            run.status = RunStatus.running
            run.celery_task_id = self.request.id
            run.started_at_utc = datetime.now(timezone.utc)
            await audit_service.log_event(
                db,
                event_type="RECON_RUN_STARTED",
                entity_id=run.run_id,
                entity_type="reconciliation_run",
                actor=triggered_by,
                correlation_id=str(uuid.uuid4()),
            )
            await db.commit()

        async with session_maker() as db:
            return await engine_instance.run(run_id, db, _progress)

    try:
        result = asyncio.run(_run())
        return {
            "matched_count": result.matched_count,
            "flagged_count": result.flagged_count,
            "exposure": result.total_monetary_exposure,
        }
    except Exception as exc:
        async def _fail():
            async with session_maker() as db:
                run = await db.get(ReconciliationRun, run_id)
                if run:
                    if self.request.retries >= self.max_retries:
                        run.status = RunStatus.failed
                        run.error_message = str(exc)
                    else:
                        run.status = RunStatus.retrying
                    await db.commit()

        asyncio.run(_fail())
        raise self.retry(exc=exc)
