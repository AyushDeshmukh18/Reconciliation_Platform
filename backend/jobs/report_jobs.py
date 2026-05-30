import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.config import get_settings
from backend.jobs.celery_app import celery_app
from backend.reporting.report_service import report_service


def _get_session_maker():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    return async_sessionmaker(engine, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=3, name="backend.jobs.report_jobs.generate_report_task")
def generate_report_task(self, run_id: str, fmt: str, requested_by: str):
    session_maker = _get_session_maker()

    async def _generate():
        async with session_maker() as db:
            self.update_state(state="PROGRESS", meta={"progress_percent": 30, "message": "Generating report"})
            meta = await report_service.generate(db, run_id, fmt, requested_by)
            self.update_state(state="PROGRESS", meta={"progress_percent": 100, "message": "Report ready"})
            return meta

    return asyncio.run(_generate())
