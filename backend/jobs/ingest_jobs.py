import asyncio
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.config import get_settings
from backend.ingestion.pipeline import ingest_bank_file, ingest_platform_file
from backend.jobs.celery_app import celery_app


def _get_session_maker():
    settings = get_settings()
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    return async_sessionmaker(engine, expire_on_commit=False)


def _run_async(coro):
    return asyncio.run(coro)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30, name="backend.jobs.ingest_jobs.ingest_platform_file_task")
def ingest_platform_file_task(self, file_path: str, file_hash: str, run_id: str, triggered_by: str):
    try:
        self.update_state(state="PROGRESS", meta={"progress_percent": 10, "message": "Reading platform file"})
        path = Path(file_path)
        file_bytes = path.read_bytes()
        session_maker = _get_session_maker()

        async def _ingest():
            async with session_maker() as db:
                result = await ingest_platform_file(
                    file_bytes,
                    file_hash,
                    path.name,
                    db,
                    actor=triggered_by,
                    correlation_id=uuid.uuid4(),
                )
                return {"accepted": result.accepted, "rejected": result.rejected}

        outcome = _run_async(_ingest())
        self.update_state(
            state="PROGRESS",
            meta={
                "progress_percent": 100,
                "message": f"Platform ingestion complete — {outcome['accepted']} accepted, {outcome['rejected']} rejected",
            },
        )
        return outcome
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30, name="backend.jobs.ingest_jobs.ingest_bank_file_task")
def ingest_bank_file_task(self, file_path: str, file_hash: str, run_id: str, triggered_by: str):
    try:
        self.update_state(state="PROGRESS", meta={"progress_percent": 10, "message": "Reading bank file"})
        path = Path(file_path)
        file_bytes = path.read_bytes()
        session_maker = _get_session_maker()

        async def _ingest():
            async with session_maker() as db:
                result = await ingest_bank_file(
                    file_bytes,
                    file_hash,
                    path.name,
                    db,
                    actor=triggered_by,
                    correlation_id=uuid.uuid4(),
                )
                return {"accepted": result.accepted, "rejected": result.rejected}

        outcome = _run_async(_ingest())
        self.update_state(
            state="PROGRESS",
            meta={
                "progress_percent": 100,
                "message": f"Bank ingestion complete — {outcome['accepted']} accepted, {outcome['rejected']} rejected",
            },
        )
        return outcome
    except Exception as exc:
        raise self.retry(exc=exc)
