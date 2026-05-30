import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class SettlementStatus(str, enum.Enum):
    settled = "settled"
    reversed = "reversed"
    returned = "returned"
    held = "held"


class BankSettlement(Base):
    __tablename__ = "bank_settlements"

    settlement_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    batch_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    transaction_reference: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    settled_amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fee_amount_minor_units: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    net_settled_amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)
    value_date_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    processing_date_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    settlement_status: Mapped[SettlementStatus] = mapped_column(
        Enum(SettlementStatus, create_constraint=False), nullable=False
    )
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    batch_sequence_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    raw_record: Mapped[dict] = mapped_column(nullable=False)

    __table_args__ = (
        Index("ix_bank_settlement_batch_value", "batch_id", "value_date_utc"),
        Index("ix_bank_settlements_net_settled_amount_minor_units", "net_settled_amount_minor_units"),
        Index("ix_bank_settlements_processing_date_utc", "processing_date_utc"),
    )
