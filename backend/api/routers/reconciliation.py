import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.models.reconciliation_result import GapType, ReconciliationResult
from backend.api.models.reconciliation_run import ReconciliationRun, RunStatus
from backend.api.schemas.reconciliation import (
    GapTypeSummary,
    IngestResponse,
    ReconciliationRunCreate,
    ReconciliationRunResponse,
)
from backend.audit.audit_service import audit_service
from backend.config import get_settings
from backend.db.base import get_db
from backend.jobs.ingest_jobs import ingest_bank_file_task, ingest_platform_file_task
from backend.jobs.local_tasks import (
    run_local_bank_ingest,
    run_local_platform_ingest,
    set_job,
    run_local_reconciliation,
)
from backend.jobs.reconciliation_jobs import run_reconciliation_task

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])
logger = logging.getLogger(__name__)


async def _save_upload_file(file: UploadFile, uploads_dir: Path, max_size: int = 100 * 1024 * 1024) -> tuple[Path, str, int]:
    uploads_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(file.filename or "upload.csv").name
    temp_path = uploads_dir / f"{uuid.uuid4().hex}.tmp"
    digest = hashlib.sha256()
    size = 0

    with temp_path.open("wb") as fp:
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_size:
                raise HTTPException(413, "File exceeds 100MB limit")
            digest.update(chunk)
            await asyncio.to_thread(fp.write, chunk)

    file_hash = digest.hexdigest()
    dest = uploads_dir / f"{file_hash}_{filename}"
    if temp_path != dest:
        temp_path.replace(dest)

    return dest, file_hash, size


def _run_to_response(run: ReconciliationRun, breakdown: dict | None = None) -> ReconciliationRunResponse:
    return ReconciliationRunResponse(
        run_id=run.run_id,
        triggered_by=run.triggered_by,
        started_at_utc=run.started_at_utc,
        completed_at_utc=run.completed_at_utc,
        status=run.status.value,
        total_records=run.total_records,
        matched_count=run.matched_count,
        unmatched_count=run.unmatched_count,
        partially_matched_count=run.partially_matched_count,
        flagged_count=run.flagged_count,
        total_monetary_exposure_minor_units=run.total_monetary_exposure_minor_units,
        celery_task_id=run.celery_task_id,
        error_message=run.error_message,
        idempotency_key=run.idempotency_key,
        date_range_start=run.date_range_start,
        date_range_end=run.date_range_end,
        progress_percent=run.progress_percent or 0.0,
        progress_message=run.progress_message,
        gap_type_breakdown=breakdown or {},
    )


async def _gap_breakdown(db: AsyncSession, run_id: str) -> dict[str, GapTypeSummary]:
    batch = await _gap_breakdown_batch(db, [run_id])
    return batch.get(run_id, {})


async def _gap_breakdown_batch(
    db: AsyncSession, run_ids: list[str]
) -> dict[str, dict[str, GapTypeSummary]]:
    if not run_ids:
        return {}
    rows = (
        await db.execute(
            select(
                ReconciliationResult.run_id,
                ReconciliationResult.gap_type,
                func.count(),
                func.coalesce(func.sum(func.abs(ReconciliationResult.monetary_difference_minor_units)), 0),
            )
            .where(ReconciliationResult.run_id.in_(run_ids))
            .group_by(ReconciliationResult.run_id, ReconciliationResult.gap_type)
        )
    ).all()
    grouped: dict[str, list] = {run_id: [] for run_id in run_ids}
    for run_id, gap_type, count, exposure in rows:
        grouped.setdefault(run_id, []).append((gap_type, count, exposure))
    result: dict[str, dict[str, GapTypeSummary]] = {}
    for run_id, entries in grouped.items():
        total = sum(entry[1] for entry in entries) or 1
        result[run_id] = {
            entry[0].value: GapTypeSummary(
                count=entry[1],
                monetary_exposure_minor_units=int(entry[2]),
                percentage=round(entry[1] / total * 100, 2),
            )
            for entry in entries
        }
    return result


@router.post("/runs", response_model=ReconciliationRunResponse)
async def create_run(
    body: ReconciliationRunCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.RECON_DUPLICATE_WINDOW_SECONDS)
    existing = await db.scalar(
        select(ReconciliationRun).where(
            ReconciliationRun.idempotency_key == body.idempotency_key,
            ReconciliationRun.started_at_utc >= cutoff,
        )
    )
    if existing:
        breakdown = await _gap_breakdown(db, existing.run_id)
        return _run_to_response(existing, breakdown)

    run = ReconciliationRun(
        run_id=str(uuid.uuid4()),
        triggered_by="system",
        started_at_utc=datetime.now(timezone.utc),
        status=RunStatus.queued,
        idempotency_key=body.idempotency_key,
        date_range_start=body.date_range_start,
        date_range_end=body.date_range_end,
    )
    db.add(run)
    await db.flush()

    task_id = None
    if settings.APP_ENV != "development":
        try:
            task = run_reconciliation_task.delay(str(run.run_id), "system")
            task_id = task.id
        except Exception as exc:
            logger.warning("Celery unavailable, falling back to local background reconciliation: %s", exc)

    if not task_id:
        task_id = str(uuid.uuid4())
        set_job(task_id, status="PENDING", progress_percent=0, message="Queued")
        background_tasks.add_task(
            run_local_reconciliation,
            task_id,
            str(run.run_id),
            "system",
        )

    run.celery_task_id = task_id

    await audit_service.log_event(
        db,
        event_type="RECON_RUN_QUEUED",
        entity_id=run.run_id,
        entity_type="reconciliation_run",
        actor="system",
        correlation_id=str(uuid.UUID(request.state.correlation_id)),
        after_state={"run_id": str(run.run_id)},
    )
    await db.commit()
    return _run_to_response(run)


@router.get("/runs", response_model=list[ReconciliationRunResponse])
async def list_runs(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    offset = (page - 1) * page_size
    runs = (
        await db.scalars(
            select(ReconciliationRun).order_by(ReconciliationRun.started_at_utc.desc()).offset(offset).limit(page_size)
        )
    ).all()
    logger.info(f"list_runs: returning {len(runs)} runs")
    breakdowns = await _gap_breakdown_batch(db, [run.run_id for run in runs])
    return [_run_to_response(run, breakdowns.get(run.run_id, {})) for run in runs]


@router.get("/runs/{run_id}", response_model=ReconciliationRunResponse)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(ReconciliationRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    breakdown = await _gap_breakdown(db, run.run_id)
    return _run_to_response(run, breakdown)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(ReconciliationRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status not in (RunStatus.queued, RunStatus.running):
        raise HTTPException(400, "Run cannot be cancelled")
    run.status = RunStatus.failed
    run.error_message = "Cancelled by user"
    run.completed_at_utc = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "cancelled"}


async def _handle_upload(
    file: UploadFile,
    upload_type: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
) -> IngestResponse:
    settings = get_settings()
    uploads_dir = Path(settings.UPLOADS_DIR)
    if not uploads_dir.is_absolute():
        uploads_dir = Path(__file__).resolve().parents[2] / uploads_dir

    dest, file_hash, size = await _save_upload_file(file, uploads_dir)

    await audit_service.log_event(
        db,
        event_type="FILE_UPLOADED",
        entity_id=str(uuid.uuid5(uuid.NAMESPACE_OID, file_hash)),
        entity_type=upload_type,
        actor="system",
        correlation_id=str(uuid.UUID(request.state.correlation_id)),
        file_hash=file_hash,
        after_state={"filename": dest.name, "size": size},
    )
    await db.commit()

    filename = Path(file.filename or "upload.csv").name

    content = await asyncio.to_thread(dest.read_bytes)

    est = max(1, size // 500)
    correlation_id = uuid.UUID(request.state.correlation_id)

    if settings.APP_ENV != "development":
        try:
            if upload_type == "platform_file":
                task = ingest_platform_file_task.delay(str(dest), file_hash, str(correlation_id), "system")
            else:
                task = ingest_bank_file_task.delay(str(dest), file_hash, str(correlation_id), "system")
            return IngestResponse(task_id=task.id, file_hash=file_hash, status="queued", record_count_estimated=est)
        except Exception as exc:
            logger.warning("Celery unavailable, falling back to local background ingest: %s", exc)

    task_id = str(uuid.uuid4())
    set_job(task_id, status="PENDING", progress_percent=0, message="Queued")

    if upload_type == "platform_file":
        background_tasks.add_task(
            run_local_platform_ingest,
            task_id,
            content,
            file_hash,
            filename,
            "system",
            correlation_id,
        )
    else:
        background_tasks.add_task(
            run_local_bank_ingest,
            task_id,
            content,
            file_hash,
            filename,
            "system",
            correlation_id,
        )

    return IngestResponse(task_id=task_id, file_hash=file_hash, status="queued", record_count_estimated=est)


@router.post("/ingest/platform", response_model=IngestResponse)
async def ingest_platform(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _handle_upload(file, "platform_file", request, background_tasks, db)


@router.post("/ingest/bank", response_model=IngestResponse)
async def ingest_bank(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    return await _handle_upload(file, "bank_file", request, background_tasks, db)
