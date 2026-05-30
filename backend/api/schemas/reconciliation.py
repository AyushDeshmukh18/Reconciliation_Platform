from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GapTypeSummary(BaseModel):
    count: int
    monetary_exposure_minor_units: int
    percentage: float


class ReconciliationRunCreate(BaseModel):
    idempotency_key: str
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None


class ReconciliationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    triggered_by: str
    started_at_utc: datetime
    completed_at_utc: datetime | None
    status: str
    total_records: int
    matched_count: int
    unmatched_count: int
    partially_matched_count: int
    flagged_count: int
    total_monetary_exposure_minor_units: int
    celery_task_id: str | None = None
    error_message: str | None = None
    idempotency_key: str
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    progress_percent: float = 0.0
    progress_message: str | None = None
    gap_type_breakdown: dict[str, GapTypeSummary] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    task_id: str
    file_hash: str
    status: str
    record_count_estimated: int = 0
    accepted: int | None = None
    rejected: int | None = None


class JobProgressResponse(BaseModel):
    task_id: str
    status: str
    progress_percent: float
    message: str
    eta_seconds: int | None = None
