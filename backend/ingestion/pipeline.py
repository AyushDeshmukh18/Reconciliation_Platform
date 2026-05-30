import uuid
import logging
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.models.bank_settlement import BankSettlement, SettlementStatus
from backend.api.models.platform_transaction import PlatformTransaction, TransactionStatus
from backend.audit.audit_service import audit_service
from backend.config import get_settings
from backend.ingestion.parsers import detect_and_parse
from backend.ingestion.validators import BankSettlementValidator, PlatformTransactionValidator, ValidationError

logger = logging.getLogger(__name__)



BATCH_FLUSH_SIZE = 100





@dataclass

class IngestionResult:

    total: int = 0

    accepted: int = 0

    rejected: int = 0

    errors: list[ValidationError] = field(default_factory=list)





async def ingest_platform_file(
    file_bytes: bytes,
    file_hash: str,
    filename: str,
    db: AsyncSession,
    actor: str = "system",
    correlation_id: uuid.UUID | None = None,
) -> IngestionResult:
    settings = get_settings()
    correlation_id = correlation_id or uuid.uuid4()
    logger.info("Starting platform file ingestion: %s (hash: %s, correlation_id: %s)", filename, file_hash, correlation_id)
    records, _parse_errors = detect_and_parse(file_bytes, filename)
    logger.info("Parsed %d records from platform file %s", len(records), filename)
    validator = PlatformTransactionValidator(settings.DEFAULT_CURRENCY, settings.RECON_LOOKBACK_DAYS)
    result = IngestionResult(total=len(records))
    seen_tx_ids: set[uuid.UUID] = set()
    pending: list = []

    for i, record in enumerate(records):
        validated, errors = validator.validate_record(record, i)
        if errors:
            result.errors.extend(errors)
            result.rejected += 1
            continue
        if validated.transaction_id in seen_tx_ids:
            result.rejected += 1
            continue
        seen_tx_ids.add(validated.transaction_id)
        pending.append(validated)

    logger.info("Validated %d records, %d pending insertion, %d rejected so far", len(records), len(pending), result.rejected)

    if pending:
            pending_ids = [str(item.transaction_id) for item in pending]
            existing_ids = set(
                await db.scalars(
                    select(PlatformTransaction.transaction_id).where(
                        PlatformTransaction.transaction_id.in_(pending_ids)
                    )
                )
            )
            logger.info("Found %d existing platform transaction IDs, skipping them", len(existing_ids))
            for validated in pending:
                tx_id_str = str(validated.transaction_id)
                if tx_id_str in existing_ids:
                    result.rejected += 1
                    continue
                db.add(
                    PlatformTransaction(
                        transaction_id=tx_id_str,
                        merchant_id=validated.merchant_id,
                        amount_minor_units=validated.amount_minor_units,
                        currency_code=validated.currency_code,
                        transaction_status=TransactionStatus(validated.transaction_status),
                        created_at_utc=validated.created_at_utc,
                        idempotency_key=validated.idempotency_key,
                        parent_transaction_id=str(validated.parent_transaction_id) if validated.parent_transaction_id else None,
                        source_file_hash=file_hash,
                        raw_record=validated.raw_record,
                    )
                )
                result.accepted += 1
                if result.accepted % BATCH_FLUSH_SIZE == 0:
                    logger.debug("Flushing %d records to database", result.accepted)
                    await db.flush()



    await audit_service.log_event(
        db,
        event_type="FILE_INGESTED",
        entity_id=str(uuid.uuid5(uuid.NAMESPACE_OID, file_hash)),
        entity_type="platform_file",
        actor=actor,
        correlation_id=str(correlation_id),
        after_state={
            "total": result.total,
            "accepted": result.accepted,
            "rejected": result.rejected,
            "file_hash": file_hash,
        },
        file_hash=file_hash,
    )
    await db.commit()
    logger.info("Platform file ingestion complete for %s: total=%d, accepted=%d, rejected=%d", filename, result.total, result.accepted, result.rejected)
    return result





async def ingest_bank_file(
    file_bytes: bytes,
    file_hash: str,
    filename: str,
    db: AsyncSession,
    actor: str = "system",
    correlation_id: uuid.UUID | None = None,
) -> IngestionResult:
    from datetime import datetime, timezone

    settings = get_settings()
    correlation_id = correlation_id or uuid.uuid4()
    logger.info("Starting bank file ingestion: %s (hash: %s, correlation_id: %s)", filename, file_hash, correlation_id)
    records, _ = detect_and_parse(file_bytes, filename)
    logger.info("Parsed %d records from bank file %s", len(records), filename)
    validator = BankSettlementValidator(settings.DEFAULT_CURRENCY, settings.RECON_LOOKBACK_DAYS)
    result = IngestionResult(total=len(records))
    pending: list = []

    for i, record in enumerate(records):
        validated, errors = validator.validate_record(record, i)
        if errors:
            result.errors.extend(errors)
            result.rejected += 1
            continue
        if validated is not None:
            pending.append(validated)

    logger.info("Validated %d records, %d pending insertion, %d rejected so far", len(records), len(pending), result.rejected)

    if validator.is_all_duplicates():
        logger.error("All records in bank file %s are duplicates, rejecting entire file", filename)
        raise ValueError("ALL_DUPLICATES_REJECTED")

    for validated in pending:
            db.add(
                BankSettlement(
                    settlement_id=str(validated.settlement_id),
                    batch_id=validated.batch_id,
                    transaction_reference=validated.transaction_reference,
                    settled_amount_minor_units=validated.settled_amount_minor_units,
                    fee_amount_minor_units=validated.fee_amount_minor_units,
                    net_settled_amount_minor_units=validated.net_settled_amount_minor_units,
                    value_date_utc=validated.value_date_utc,
                    processing_date_utc=validated.processing_date_utc,
                    settlement_status=SettlementStatus(validated.settlement_status),
                    file_hash=file_hash,
                    batch_sequence_number=validated.batch_sequence_number,
                    raw_record=validated.raw_record,
                )
            )
            result.accepted += 1
            if result.accepted % BATCH_FLUSH_SIZE == 0:
                logger.debug("Flushing %d records to database", result.accepted)
                await db.flush()



    now = datetime.now(timezone.utc)

    if now.hour >= settings.RECON_SETTLEMENT_FILE_CUTOFF_HOUR:

        await audit_service.log_event(
            db,
            event_type="LATE_SETTLEMENT_FILE",
            entity_id=str(uuid.uuid5(uuid.NAMESPACE_OID, file_hash)),
            entity_type="bank_file",
            actor=actor,
            correlation_id=str(correlation_id),
            after_state={"file_hash": file_hash, "hour": now.hour},
            file_hash=file_hash,
        )

    await audit_service.log_event(
        db,
        event_type="FILE_INGESTED",
        entity_id=str(uuid.uuid5(uuid.NAMESPACE_OID, file_hash)),
        entity_type="bank_file",
        actor=actor,
        correlation_id=str(correlation_id),
        after_state={
            "total": result.total,
            "accepted": result.accepted,
            "rejected": result.rejected,
            "file_hash": file_hash,
        },
        file_hash=file_hash,
    )

    await db.commit()
    logger.info("Bank file ingestion complete for %s: total=%d, accepted=%d, rejected=%d", filename, result.total, result.accepted, result.rejected)

    return result


