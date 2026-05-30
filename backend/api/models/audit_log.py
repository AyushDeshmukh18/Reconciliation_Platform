import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    event_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(nullable=True)
    after_state: Mapped[dict | None] = mapped_column(nullable=True)
    created_at_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )
    correlation_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_audit_entity_created", "entity_id", "created_at_utc"),
    )
