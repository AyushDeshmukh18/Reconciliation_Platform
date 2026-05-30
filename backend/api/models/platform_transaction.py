import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    reversed = "reversed"
    voided = "voided"


class PlatformTransaction(Base):
    __tablename__ = "platform_transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    merchant_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    transaction_status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, create_constraint=False), nullable=False
    )
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(256), unique=True, index=True, nullable=True)
    parent_transaction_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("platform_transactions.transaction_id"), nullable=True
    )
    source_file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_record: Mapped[dict] = mapped_column(nullable=False)

    parent: Mapped["PlatformTransaction | None"] = relationship(
        "PlatformTransaction", remote_side=[transaction_id]
    )

    __table_args__ = (
        Index("ix_platform_tx_merchant_created", "merchant_id", "created_at_utc"),
        Index("ix_platform_transactions_amount_minor_units", "amount_minor_units"),
        Index("ix_platform_transactions_parent_transaction_id", "parent_transaction_id"),
    )
