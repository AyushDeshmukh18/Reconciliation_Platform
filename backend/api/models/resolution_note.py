import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class ResolutionNote(Base):
    __tablename__ = "resolution_notes"

    note_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reconciliation_results.result_id"), nullable=False
    )
    analyst_id: Mapped[str] = mapped_column(String(128), nullable=False)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    result: Mapped["ReconciliationResult"] = relationship(
        "ReconciliationResult", back_populates="resolution_notes"
    )
