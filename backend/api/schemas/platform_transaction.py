from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlatformTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: UUID
    merchant_id: str
    amount_minor_units: int
    currency_code: str
    transaction_status: str
    created_at_utc: datetime
    idempotency_key: str | None
    parent_transaction_id: UUID | None
    source_file_hash: str


class BankSettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    settlement_id: UUID
    batch_id: str
    transaction_reference: str
    settled_amount_minor_units: int
    fee_amount_minor_units: int
    net_settled_amount_minor_units: int
    value_date_utc: datetime
    processing_date_utc: datetime
    settlement_status: str
    file_hash: str
    batch_sequence_number: int
