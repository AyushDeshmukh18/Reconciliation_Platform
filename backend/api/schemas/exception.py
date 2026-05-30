from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReconStatus(str, Enum):
    unprocessed = "unprocessed"
    matched = "matched"
    partially_matched = "partially_matched"
    flagged = "flagged"
    manually_resolved = "manually_resolved"
    closed = "closed"


class ExceptionListItem(BaseModel):
    result_id: UUID
    run_id: UUID
    gap_type: str
    gap_confidence: float
    recon_status: str
    monetary_difference_minor_units: int
    platform_transaction_id: UUID | None
    bank_settlement_id: UUID | None
    created_at_utc: datetime
    merchant_id: str | None = None
    requires_secondary_review: bool = False


class PlatformTransactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: UUID
    merchant_id: str
    amount_minor_units: int
    currency_code: str
    transaction_status: str
    created_at_utc: datetime
    idempotency_key: str | None
    parent_transaction_id: UUID | None


class BankSettlementSchema(BaseModel):
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


class ResolutionNoteSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    note_id: UUID
    analyst_id: str
    note_text: str
    is_ai_suggested: bool
    created_at_utc: datetime


class RuleEvaluation(BaseModel):
    rule_id: str
    gap_type: str
    conditions_tested: dict[str, bool | Any] = Field(default_factory=dict)
    fired: bool
    confidence: float | None = None


from typing import Any  # noqa: E402


class ExceptionDetail(ExceptionListItem):
    platform_transaction: PlatformTransactionSchema | None = None
    bank_settlement: BankSettlementSchema | None = None
    rule_evaluation_trace: list[dict] | list[RuleEvaluation] = Field(default_factory=list)
    gap_explanation: str | None = None
    resolution_suggestion: str | None = None
    resolution_notes: list[ResolutionNoteSchema] = Field(default_factory=list)


class StatusUpdateRequest(BaseModel):
    new_status: ReconStatus
    note: str | None = None


class BulkResolveRequest(BaseModel):
    result_ids: list[UUID]
    note_text: str
    confirmation: bool


class ResolutionNoteCreate(BaseModel):
    note_text: str
    accept_ai_suggestion: bool = False


class DryRunRequest(BaseModel):
    transaction_record: dict


class DryRunResponse(BaseModel):
    rules_evaluated: list[RuleEvaluation]
    winning_rule: str | None
    gap_type: str | None
    confidence: float
