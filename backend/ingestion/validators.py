import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from backend.ingestion.normalizers import amount_to_minor_units, normalize_timestamp

ALLOWED_PLATFORM_STATUSES = {"pending", "success", "failed", "reversed", "voided"}
MAX_AMOUNT_PAISE = 500_000_000


@dataclass
class ValidationError:
    record_index: int
    error_code: str
    message: str
    field: str | None = None


@dataclass
class ValidatedPlatformRecord:
    transaction_id: uuid.UUID
    merchant_id: str
    amount_minor_units: int
    currency_code: str
    transaction_status: str
    created_at_utc: datetime
    idempotency_key: str | None
    parent_transaction_id: uuid.UUID | None
    raw_record: dict
    flagged_for_review: bool = False


@dataclass
class ValidatedBankRecord:
    settlement_id: uuid.UUID
    batch_id: str
    transaction_reference: str
    settled_amount_minor_units: int
    fee_amount_minor_units: int
    net_settled_amount_minor_units: int
    value_date_utc: datetime
    processing_date_utc: datetime
    settlement_status: str
    batch_sequence_number: int
    raw_record: dict
    is_chargeback: bool = False


class PlatformTransactionValidator:
    def __init__(self, currency: str = "INR", lookback_days: int = 120):
        self.currency = currency
        self.lookback_days = lookback_days
        self.now = datetime.now(timezone.utc)

    def validate_record(self, record: dict, index: int) -> tuple[ValidatedPlatformRecord | None, list[ValidationError]]:
        errors: list[ValidationError] = []
        tx_id_raw = record.get("transaction_id") or record.get("id")
        if not tx_id_raw:
            errors.append(ValidationError(index, "MISSING_TRANSACTION_ID", "transaction_id is required", "transaction_id"))
            return None, errors

        merchant_id = record.get("merchant_id")
        if not merchant_id:
            errors.append(ValidationError(index, "MISSING_MERCHANT", "merchant_id is required", "merchant_id"))
            return None, errors

        amount_raw = record.get("amount") or record.get("amount_minor_units")
        if amount_raw is None:
            errors.append(ValidationError(index, "MISSING_AMOUNT", "amount is required", "amount"))
            return None, errors

        try:
            if "amount_minor_units" in record and record.get("amount_minor_units") is not None:
                amount_minor = int(record["amount_minor_units"])
            else:
                amount_minor = amount_to_minor_units(amount_raw)
        except Exception:
            errors.append(ValidationError(index, "INVALID_AMOUNT", "amount must be a positive number", "amount"))
            return None, errors

        if amount_minor <= 0:
            errors.append(ValidationError(index, "ZERO_AMOUNT_REJECTED", "zero amount records rejected", "amount"))
            return None, errors

        flagged = amount_minor > MAX_AMOUNT_PAISE

        ts_raw = record.get("timestamp") or record.get("created_at") or record.get("created_at_utc")
        if not ts_raw:
            errors.append(ValidationError(index, "MISSING_TIMESTAMP", "timestamp is required", "timestamp"))
            return None, errors
        try:
            created_at = normalize_timestamp(str(ts_raw))
        except Exception:
            errors.append(ValidationError(index, "INVALID_TIMESTAMP", "invalid ISO 8601 timestamp", "timestamp"))
            return None, errors

        if created_at < self.now - timedelta(days=self.lookback_days) or created_at > self.now + timedelta(days=1):
            errors.append(ValidationError(index, "TIMESTAMP_OUT_OF_RANGE", "timestamp out of allowed range", "timestamp"))
            return None, errors

        status = str(record.get("status") or record.get("transaction_status", "success")).lower()
        if status not in ALLOWED_PLATFORM_STATUSES:
            errors.append(ValidationError(index, "INVALID_STATUS", f"status must be one of {ALLOWED_PLATFORM_STATUSES}", "status"))
            return None, errors

        try:
            tx_id = uuid.UUID(str(tx_id_raw))
        except ValueError:
            tx_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(tx_id_raw))

        parent_id = None
        if record.get("parent_transaction_id"):
            try:
                parent_id = uuid.UUID(str(record["parent_transaction_id"]))
            except ValueError:
                parent_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(record["parent_transaction_id"]))

        return ValidatedPlatformRecord(
            transaction_id=tx_id,
            merchant_id=str(merchant_id),
            amount_minor_units=amount_minor,
            currency_code=str(record.get("currency_code", self.currency))[:3],
            transaction_status=status,
            created_at_utc=created_at,
            idempotency_key=record.get("idempotency_key"),
            parent_transaction_id=parent_id,
            raw_record=record,
            flagged_for_review=flagged,
        ), errors


class BankSettlementValidator:
    def __init__(self, currency: str = "INR", lookback_days: int = 120):
        self.currency = currency
        self.lookback_days = lookback_days
        self.now = datetime.now(timezone.utc)
        self.seen_keys: set[str] = set()
        self.duplicate_count = 0
        self.total_count = 0

    def validate_record(self, record: dict, index: int) -> tuple[ValidatedBankRecord | None, list[ValidationError]]:
        errors: list[ValidationError] = []
        self.total_count += 1

        batch_id = record.get("batch_id")
        if not batch_id:
            errors.append(ValidationError(index, "MISSING_BATCH", "batch_id is required", "batch_id"))
            return None, errors

        tx_ref = record.get("transaction_reference") or record.get("transaction_id")
        if not tx_ref:
            errors.append(ValidationError(index, "MISSING_REFERENCE", "transaction_reference required", "transaction_reference"))
            return None, errors

        dup_key = f"{batch_id}:{tx_ref}:{record.get('settled_amount')}"
        if dup_key in self.seen_keys:
            self.duplicate_count += 1
        self.seen_keys.add(dup_key)

        amount_raw = record.get("settled_amount") or record.get("settled_amount_minor_units")
        if amount_raw is None:
            errors.append(ValidationError(index, "MISSING_AMOUNT", "settled_amount required", "settled_amount"))
            return None, errors

        try:
            if record.get("settled_amount_minor_units") is not None:
                settled_minor = int(record["settled_amount_minor_units"])
            else:
                settled_minor = amount_to_minor_units(amount_raw, bank_floor=True)
        except Exception:
            errors.append(ValidationError(index, "INVALID_AMOUNT", "invalid settled_amount", "settled_amount"))
            return None, errors

        is_chargeback = settled_minor < 0

        fee_minor = 0
        if record.get("fee_amount_minor_units") is not None:
            fee_minor = int(record["fee_amount_minor_units"])
        elif record.get("fee_amount") is not None:
            fee_minor = amount_to_minor_units(record["fee_amount"], bank_floor=True)

        net_minor = record.get("net_settled_amount_minor_units")
        if net_minor is not None:
            net_minor = int(net_minor)
        else:
            net_minor = settled_minor - fee_minor

        value_raw = record.get("value_date") or record.get("value_date_utc")
        if not value_raw:
            errors.append(ValidationError(index, "MISSING_VALUE_DATE", "value_date required", "value_date"))
            return None, errors
        try:
            value_date = normalize_timestamp(str(value_raw))
        except Exception:
            errors.append(ValidationError(index, "INVALID_VALUE_DATE", "invalid value_date", "value_date"))
            return None, errors

        proc_raw = record.get("processing_date") or record.get("processing_date_utc") or value_raw
        try:
            processing_date = normalize_timestamp(str(proc_raw))
        except Exception:
            processing_date = value_date

        if value_date < self.now - timedelta(days=self.lookback_days) or value_date > self.now + timedelta(days=1):
            errors.append(ValidationError(index, "TIMESTAMP_OUT_OF_RANGE", "value_date out of range", "value_date"))
            return None, errors

        status = str(record.get("settlement_status") or record.get("status", "settled")).lower()
        allowed = {"settled", "reversed", "returned", "held"}
        if status not in allowed:
            status = "settled"

        settlement_id_raw = record.get("settlement_id")
        if settlement_id_raw:
            try:
                settlement_id = uuid.UUID(str(settlement_id_raw))
            except ValueError:
                settlement_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(settlement_id_raw))
        else:
            settlement_id = uuid.uuid4()

        return ValidatedBankRecord(
            settlement_id=settlement_id,
            batch_id=str(batch_id),
            transaction_reference=str(tx_ref),
            settled_amount_minor_units=settled_minor,
            fee_amount_minor_units=fee_minor,
            net_settled_amount_minor_units=net_minor,
            value_date_utc=value_date,
            processing_date_utc=processing_date,
            settlement_status=status,
            batch_sequence_number=int(record.get("batch_sequence_number", 0)),
            raw_record=record,
            is_chargeback=is_chargeback,
        ), errors

    def is_all_duplicates(self) -> bool:
        return self.total_count > 0 and self.duplicate_count == self.total_count
