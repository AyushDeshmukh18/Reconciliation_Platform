"""In-process background jobs for development (no Celery required)."""

from __future__ import annotations

import asyncio
import uuid
import logging
from typing import Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from backend.db.base import AsyncSessionLocal
from backend.ingestion.pipeline import ingest_bank_file, ingest_platform_file
from backend.api.models.reconciliation_run import ReconciliationRun, RunStatus
from backend.engine.reconciliation_engine import ReconciliationEngine
from backend.audit.audit_service import audit_service

_local_jobs: dict[str, dict[str, Any]] = {}
_background_tasks: set[asyncio.Task] = set()


def get_local_job(task_id: str) -> dict[str, Any] | None:
    return _local_jobs.get(task_id)


def set_job(task_id: str, **fields: Any) -> None:
    current = _local_jobs.get(task_id, {})
    current.update(fields)
    _local_jobs[task_id] = current

# Keep backward compatibility
_set_job = set_job


async def run_local_platform_ingest(
    task_id: str,
    content: bytes,
    file_hash: str,
    filename: str,
    actor: str,
    correlation_id: uuid.UUID,
) -> None:
    logger.info("Starting platform file ingestion for task %s (filename: %s)", task_id, filename)
    await asyncio.sleep(0.1)
    set_job(task_id, status="PROGRESS", progress_percent=5, message="Validating platform file")
    try:
        async with AsyncSessionLocal() as db:
            set_job(task_id, progress_percent=25, message="Writing records to database")
            result = await ingest_platform_file(
                content, file_hash, filename, db, actor=actor, correlation_id=correlation_id
            )
        logger.info("Platform file ingestion complete for task %s: %d accepted, %d rejected", task_id, result.accepted, result.rejected)
        set_job(
            task_id,
            status="SUCCESS",
            progress_percent=100,
            message=f"Ingestion complete — {result.accepted} accepted, {result.rejected} rejected",
            result={"accepted": result.accepted, "rejected": result.rejected},
        )
    except Exception as exc:
        logger.error("Platform file ingestion failed for task %s: %s", task_id, exc, exc_info=True)
        set_job(task_id, status="FAILURE", progress_percent=100, message=str(exc))


async def run_local_bank_ingest(
    task_id: str,
    content: bytes,
    file_hash: str,
    filename: str,
    actor: str,
    correlation_id: uuid.UUID,
) -> None:
    logger.info("Starting bank file ingestion for task %s (filename: %s)", task_id, filename)
    await asyncio.sleep(0.1)
    set_job(task_id, status="PROGRESS", progress_percent=5, message="Validating bank file")
    try:
        async with AsyncSessionLocal() as db:
            set_job(task_id, progress_percent=25, message="Writing records to database")
            result = await ingest_bank_file(
                content, file_hash, filename, db, actor=actor, correlation_id=correlation_id
            )
        logger.info("Bank file ingestion complete for task %s: %d accepted, %d rejected", task_id, result.accepted, result.rejected)
        set_job(
            task_id,
            status="SUCCESS",
            progress_percent=100,
            message=f"Ingestion complete — {result.accepted} accepted, {result.rejected} rejected",
            result={"accepted": result.accepted, "rejected": result.rejected},
        )
    except Exception as exc:
        logger.error("Bank file ingestion failed for task %s: %s", task_id, exc, exc_info=True)
        set_job(task_id, status="FAILURE", progress_percent=100, message=str(exc))


async def run_local_reconciliation(
    task_id: str,
    run_id: str,
    triggered_by: str,
) -> None:
    logger.info("Starting reconciliation run (task %s, run %s)", task_id, run_id)
    await asyncio.sleep(0.1)
    set_job(task_id, status="PROGRESS", progress_percent=0, message="Starting reconciliation")
    try:
        engine_instance = ReconciliationEngine()

        async def _progress(pct: float, message: str):
            set_job(task_id, progress_percent=pct, message=message)
            async with AsyncSessionLocal() as db:
                run = await db.get(ReconciliationRun, run_id)
                if run:
                    run.progress_percent = pct
                    run.progress_message = message
                    await db.commit()

        async with AsyncSessionLocal() as db:
            run = await db.get(ReconciliationRun, run_id)
            if not run:
                raise ValueError("Run not found")
            run.status = RunStatus.running
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

        logger.info("Running reconciliation engine for run %s", run_id)
        async with AsyncSessionLocal() as db:
            result = await engine_instance.run(run_id, db, _progress)

        async with AsyncSessionLocal() as db:
            run = await db.get(ReconciliationRun, run_id)
            if run:
                run.status = RunStatus.completed
                run.completed_at_utc = datetime.now(timezone.utc)
                run.total_records = (result.matched_count or 0) + (result.unmatched_count or 0) + (result.partially_matched_count or 0) + (result.flagged_count or 0)
                run.matched_count = result.matched_count
                run.unmatched_count = result.unmatched_count
                run.partially_matched_count = result.partially_matched_count
                run.flagged_count = result.flagged_count
                run.total_monetary_exposure_minor_units = result.total_monetary_exposure
                await audit_service.log_event(
                    db,
                    event_type="RECON_RUN_COMPLETED",
                    entity_id=run.run_id,
                    entity_type="reconciliation_run",
                    actor=triggered_by,
                    correlation_id=str(uuid.uuid4()),
                    after_state={"matched": run.matched_count, "flagged": run.flagged_count},
                )
                await db.commit()
        logger.info("Reconciliation run complete for run %s: matched %d, unmatched %d, partially matched %d, flagged %d", run_id, result.matched_count, result.unmatched_count, result.partially_matched_count, result.flagged_count)
        set_job(
            task_id,
            status="SUCCESS",
            progress_percent=100,
            message="Reconciliation complete",
            result={"matched_count": result.matched_count, "flagged_count": result.flagged_count},
        )
    except Exception as exc:
        logger.error("Reconciliation run failed for run %s: %s", run_id, exc, exc_info=True)
        async with AsyncSessionLocal() as db:
            run = await db.get(ReconciliationRun, run_id)
            if run:
                run.status = RunStatus.failed
                run.error_message = str(exc)
                await db.commit()
        set_job(task_id, status="FAILURE", progress_percent=100, message=str(exc))


def schedule_local_ingest(runner, *args, **kwargs) -> str:
    task_id = str(uuid.uuid4())
    set_job(task_id, status="PENDING", progress_percent=0, message="Queued")
    task = asyncio.create_task(runner(task_id, *args, **kwargs))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task_id


def schedule_local_reconciliation(runner, *args, **kwargs) -> str:
    task_id = str(uuid.uuid4())
    set_job(task_id, status="PENDING", progress_percent=0, message="Queued")
    task = asyncio.create_task(runner(task_id, *args, **kwargs))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task_id
