import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class MatchType(str, enum.Enum):
    exact = "exact"
    fuzzy = "fuzzy"
    composite = "composite"
    partial = "partial"
    unmatched = "unmatched"


class GapType(str, enum.Enum):
    timing_gap = "timing_gap"
    rounding_difference = "rounding_difference"
    duplicate_entry = "duplicate_entry"
    orphan_refund = "orphan_refund"
    partial_settlement = "partial_settlement"
    failed_reversal = "failed_reversal"
    split_settlement = "split_settlement"
    stale_retry = "stale_retry"
    settlement_truncation = "settlement_truncation"
    status_mismatch = "status_mismatch"
    idempotency_failure = "idempotency_failure"
    unclassified = "unclassified"


class ReconStatus(str, enum.Enum):
    unprocessed = "unprocessed"
    matched = "matched"
    partially_matched = "partially_matched"
    flagged = "flagged"
    manually_resolved = "manually_resolved"
    closed = "closed"


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    result_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reconciliation_runs.run_id"), index=True, nullable=False
    )
    platform_transaction_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("platform_transactions.transaction_id"), index=True, nullable=True
    )
    bank_settlement_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("bank_settlements.settlement_id"), nullable=True
    )
    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType, create_constraint=False), nullable=False
    )
    gap_type: Mapped[GapType] = mapped_column(
        Enum(GapType, create_constraint=False), index=True, nullable=False
    )
    gap_confidence: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    monetary_difference_minor_units: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    recon_status: Mapped[ReconStatus] = mapped_column(
        Enum(ReconStatus, create_constraint=False), default=ReconStatus.unprocessed, index=True, nullable=False
    )
    rule_id_fired: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_evaluation_trace: Mapped[list | dict] = mapped_column(default=list, nullable=False)
    gap_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_secondary_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    resolution_notes: Mapped[list["ResolutionNote"]] = relationship(
        "ResolutionNote", back_populates="result", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_recon_results_run_gap", "run_id", "gap_type"),
    )
