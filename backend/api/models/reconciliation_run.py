import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class RunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    retrying = "retrying"


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    run_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    triggered_by: Mapped[str] = mapped_column(String(128), nullable=False)
    started_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, create_constraint=False), default=RunStatus.queued, nullable=False
    )
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmatched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    partially_matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    flagged_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_monetary_exposure_minor_units: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    date_range_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    date_range_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    progress_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
