import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.engine.tolerance import compute_tolerance_band

from backend.api.models.bank_settlement import BankSettlement
from backend.api.models.platform_transaction import PlatformTransaction
from backend.api.models.reconciliation_result import (
    GapType,
    MatchType,
    ReconciliationResult,
    ReconStatus,
)
from backend.api.models.reconciliation_run import ReconciliationRun, RunStatus
from backend.audit.audit_service import audit_service
from backend.engine.matcher import ReconciliationMatcher
from backend.rules.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


@dataclass
class ReconciliationRunResult:
    matched_count: int
    unmatched_count: int
    partially_matched_count: int
    flagged_count: int
    total_monetary_exposure: int


def _platform_to_dict(p: PlatformTransaction) -> dict:
    return {
        "transaction_id": p.transaction_id,
        "merchant_id": p.merchant_id,
        "amount_minor_units": p.amount_minor_units,
        "transaction_status": p.transaction_status.value,
        "created_at_utc": p.created_at_utc,
        "idempotency_key": p.idempotency_key,
        "parent_transaction_id": p.parent_transaction_id,
        "raw_record": p.raw_record,
    }


def _bank_to_dict(b: BankSettlement) -> dict:
    return {
        "settlement_id": b.settlement_id,
        "batch_id": b.batch_id,
        "transaction_reference": b.transaction_reference,
        "settled_amount_minor_units": b.settled_amount_minor_units,
        "fee_amount_minor_units": b.fee_amount_minor_units,
        "net_settled_amount_minor_units": b.net_settled_amount_minor_units,
        "value_date_utc": b.value_date_utc,
        "settlement_status": b.settlement_status.value,
        "raw_record": b.raw_record,
    }


class ReconciliationEngine:
    BATCH_SIZE = 1000

    def __init__(self):
        self.matcher = ReconciliationMatcher()
        self.rule_engine = RuleEngine()

    async def run(
        self,
        run_id: str,
        db: AsyncSession,
        progress_callback=None,
    ) -> ReconciliationRunResult:
        logger.info("Starting reconciliation engine for run %s", run_id)
        run = await db.get(ReconciliationRun, run_id)
        if not run:
            logger.error("Reconciliation run %s not found in database", run_id)
            raise ValueError(f"Run {run_id} not found")

        logger.info("Preparing candidate queries for reconciliation run %s", run_id)
        platform_stmt = select(PlatformTransaction).order_by(PlatformTransaction.created_at_utc)
        bank_stmt = select(BankSettlement).order_by(BankSettlement.value_date_utc)
        if run.date_range_start:
            platform_stmt = platform_stmt.where(PlatformTransaction.created_at_utc >= run.date_range_start)
            bank_stmt = bank_stmt.where(BankSettlement.value_date_utc >= run.date_range_start)
        if run.date_range_end:
            platform_stmt = platform_stmt.where(PlatformTransaction.created_at_utc <= run.date_range_end)
            bank_stmt = bank_stmt.where(BankSettlement.value_date_utc <= run.date_range_end)

        platform_total = await db.scalar(
            select(func.count()).select_from(PlatformTransaction).where(
                *([PlatformTransaction.created_at_utc >= run.date_range_start] if run.date_range_start else []),
                *([PlatformTransaction.created_at_utc <= run.date_range_end] if run.date_range_end else []),
            )
        )
        bank_total = await db.scalar(
            select(func.count()).select_from(BankSettlement).where(
                *([BankSettlement.value_date_utc >= run.date_range_start] if run.date_range_start else []),
                *([BankSettlement.value_date_utc <= run.date_range_end] if run.date_range_end else []),
            )
        )

        logger.info(
            "Reconciliation run %s candidate set: %s platform records, %s bank records",
            run_id,
            platform_total,
            bank_total,
        )

        matched_count = 0
        partial_count = 0
        flagged_count = 0
        unmatched_count = 0
        exposure = 0
        matched_platform_ids: set[str] = set()
        matched_bank_ids: set[str] = set()
        pending_writes: list[ReconciliationResult] = []
        COMMIT_BATCH_SIZE = 500

        async def commit_pending():
            nonlocal pending_writes
            if pending_writes:
                db.add_all(pending_writes)
                await db.commit()
                pending_writes = []
                await db.rollback()

        async def write_result(
            platform,
            bank,
            match_type: MatchType,
            gap_type: GapType,
            confidence: float,
            monetary_diff: int,
            recon_status: ReconStatus,
            rule_id: str | None,
            trace: list,
        ):
            nonlocal matched_count, partial_count, flagged_count, unmatched_count, exposure, pending_writes
            result = ReconciliationResult(
                result_id=str(uuid.uuid4()),
                run_id=run_id,
                platform_transaction_id=platform.get("transaction_id") if platform else None,
                bank_settlement_id=(
                    bank.get("settlement_id") if isinstance(bank, dict) else None
                ),
                match_type=match_type,
                gap_type=gap_type,
                gap_confidence=confidence,
                monetary_difference_minor_units=monetary_diff,
                recon_status=recon_status,
                rule_id_fired=rule_id,
                rule_evaluation_trace=trace,
                requires_secondary_review=confidence < 70,
            )
            pending_writes.append(result)
            if len(pending_writes) >= COMMIT_BATCH_SIZE:
                await commit_pending()
            if recon_status == ReconStatus.matched:
                matched_count += 1
            elif recon_status == ReconStatus.partially_matched:
                partial_count += 1
            elif recon_status == ReconStatus.flagged:
                flagged_count += 1
                exposure += abs(monetary_diff)
            else:
                unmatched_count += 1
                exposure += abs(monetary_diff)

        if progress_callback:
            await progress_callback(10, "Loading records")

        # Track all transactions present in the run for rule decisions
        existing_ids = set(
            (await db.scalars(
                select(PlatformTransaction.transaction_id)
                .where(*([PlatformTransaction.created_at_utc >= run.date_range_start] if run.date_range_start else []))
                .where(*([PlatformTransaction.created_at_utc <= run.date_range_end] if run.date_range_end else []))
            )).all()
        )

        async def get_platform_batch(offset: int) -> list[PlatformTransaction]:
            stmt = platform_stmt.limit(self.BATCH_SIZE).offset(offset)
            return (await db.scalars(stmt)).all()

        async def get_exact_bank_candidates(platform_row: PlatformTransaction):
            tolerance = compute_tolerance_band(platform_row.amount_minor_units)
            stmt = select(BankSettlement).where(
                BankSettlement.transaction_reference == str(platform_row.transaction_id),
                BankSettlement.net_settled_amount_minor_units.between(
                    platform_row.amount_minor_units - tolerance,
                    platform_row.amount_minor_units + tolerance,
                ),
            )
            if run.date_range_start:
                stmt = stmt.where(BankSettlement.value_date_utc >= run.date_range_start)
            if run.date_range_end:
                stmt = stmt.where(BankSettlement.value_date_utc <= run.date_range_end)
            if matched_bank_ids:
                stmt = stmt.where(~BankSettlement.settlement_id.in_(matched_bank_ids))
            return (await db.scalars(stmt)).all()

        async def get_fuzzy_bank_candidates(platform_dict: dict):
            amount = platform_dict["amount_minor_units"]
            tolerance = compute_tolerance_band(amount)
            created_at = platform_dict["created_at_utc"]
            date_lower = created_at - timedelta(days=2)
            date_upper = created_at + timedelta(days=2)
            stmt = select(BankSettlement).where(
                BankSettlement.net_settled_amount_minor_units.between(amount - tolerance, amount + tolerance),
                BankSettlement.value_date_utc.between(date_lower, date_upper),
            )
            merchant_id = platform_dict.get("merchant_id")
            if merchant_id:
                stmt = stmt.where(BankSettlement.merchant_id == merchant_id)
            if matched_bank_ids:
                stmt = stmt.where(~BankSettlement.settlement_id.in_(matched_bank_ids))
            return (await db.scalars(stmt)).all()

        async def commit_pending():
            nonlocal pending_writes
            if pending_writes:
                db.add_all(pending_writes)
                await db.commit()
                pending_writes = []
                await db.rollback()

        async def process_platform_batch(batch):
            nonlocal matched_platform_ids, matched_bank_ids
            for platform_row in batch:
                if platform_row.transaction_id in matched_platform_ids:
                    continue
                exact_candidates = await get_exact_bank_candidates(platform_row)
                if exact_candidates:
                    bank_row = exact_candidates[0]
                    matched_platform_ids.add(platform_row.transaction_id)
                    matched_bank_ids.add(bank_row.settlement_id)
                    gap_type = GapType.status_mismatch if self.matcher._status_mismatch(_platform_to_dict(platform_row), _bank_to_dict(bank_row)) else GapType.unclassified
                    status = ReconStatus.flagged if gap_type == GapType.status_mismatch else ReconStatus.matched
                    await write_result(
                        _platform_to_dict(platform_row),
                        _bank_to_dict(bank_row),
                        MatchType.exact,
                        gap_type,
                        99.0,
                        platform_row.amount_minor_units - bank_row.net_settled_amount_minor_units,
                        status,
                        "STATUS_MISMATCH_001" if status == ReconStatus.flagged else None,
                        [],
                    )
                    continue

                fuzzy_candidates = await get_fuzzy_bank_candidates(_platform_to_dict(platform_row))
                if fuzzy_candidates:
                    best_bank = min(
                        fuzzy_candidates,
                        key=lambda bank_row: abs(platform_row.amount_minor_units - bank_row.net_settled_amount_minor_units),
                    )
                    diff = platform_row.amount_minor_units - best_bank.net_settled_amount_minor_units
                    matched_platform_ids.add(platform_row.transaction_id)
                    matched_bank_ids.add(best_bank.settlement_id)
                    await write_result(
                        _platform_to_dict(platform_row),
                        _bank_to_dict(best_bank),
                        MatchType.fuzzy,
                        GapType.unclassified,
                        80.0,
                        diff,
                        ReconStatus.matched,
                        None,
                        [],
                    )
                    continue

                unmatched_platforms.append(_platform_to_dict(platform_row))

        async def load_unmatched_bank_rows():
            stmt = bank_stmt
            if matched_bank_ids:
                stmt = stmt.where(~BankSettlement.settlement_id.in_(matched_bank_ids))
            return (await db.scalars(stmt)).all()

        logger.info("Starting candidate-driven reconciliation for run %s", run_id)
        offset = 0
        unmatched_platforms: list[dict] = []
        while True:
            batch = await get_platform_batch(offset)
            if not batch:
                break
            await process_platform_batch(batch)
            offset += self.BATCH_SIZE
            if progress_callback:
                await progress_callback(20 + min(40, int(offset / max(1, platform_total) * 40)), "Processing platform batches")

        unmatched_bank_rows = await load_unmatched_bank_rows()
        unmatched_bank = [_bank_to_dict(b) for b in unmatched_bank_rows if b.settlement_id not in matched_bank_ids]

        if progress_callback:
            await progress_callback(60, "Platform pass complete")

        logger.info("Starting Pass 3: Composite matching for run %s with %d unmatched platform and %d unmatched bank", run_id, len(unmatched_platforms), len(unmatched_bank))
        p3, (up, ub) = await self.matcher.pass_3_composite_match(unmatched_platforms, unmatched_bank)
        logger.info("Pass 3 found %d composite matches for run %s", len(p3), run_id)
        for m in p3:
            pid = m.platform.get("transaction_id")
            if pid and pid in matched_platform_ids:
                continue
            if pid:
                matched_platform_ids.add(pid)
            bank_entry = m.bank if isinstance(m.bank, dict) else (m.bank[0] if m.bank else None)
            if bank_entry and bank_entry.get("settlement_id"):
                matched_bank_ids.add(bank_entry["settlement_id"])
            await write_result(
                m.platform if isinstance(m.platform, dict) and "amount_minor_units" in m.platform else None,
                bank_entry,
                MatchType.composite if m.match_type == "composite" else MatchType.unmatched,
                GapType(m.gap_type) if m.gap_type else GapType.unclassified,
                m.confidence,
                m.monetary_difference,
                ReconStatus.flagged,
                f"{m.gap_type.upper()}_001" if m.gap_type else None,
                [],
            )
            if isinstance(m.bank, list):
                for b in m.bank:
                    matched_bank_ids.add(b["settlement_id"])
            elif isinstance(m.bank, dict):
                matched_bank_ids.add(m.bank.get("settlement_id"))

        if progress_callback:
            await progress_callback(85, "Composite matching complete")

        residual_platforms = [p for p in unmatched_platforms if p["transaction_id"] not in matched_platform_ids]
        residual_banks = [b for b in unmatched_bank if b["settlement_id"] not in matched_bank_ids]

        for p in residual_platforms:
            parent_exists = p.get("parent_transaction_id") in existing_ids
            classification = self.rule_engine.evaluate(
                p,
                None,
                {"parent_exists": parent_exists, "run_date_range": (run.date_range_start, run.date_range_end)},
            )
            await write_result(
                p,
                None,
                MatchType.unmatched,
                GapType(classification.gap_type),
                classification.confidence,
                p["amount_minor_units"],
                ReconStatus.flagged,
                classification.rule_id,
                classification.trace,
            )

        for b in residual_banks:
            classification = self.rule_engine.evaluate(None, b, {})
            await write_result(
                None,
                b,
                MatchType.unmatched,
                GapType(classification.gap_type),
                classification.confidence,
                -b["net_settled_amount_minor_units"],
                ReconStatus.flagged,
                classification.rule_id,
                classification.trace,
            )

        await commit_pending()
        logger.info("Reconciliation run %s complete: matched=%d, partially_matched=%d, flagged=%d, unmatched=%d, exposure=%d", run_id, matched_count, partial_count, flagged_count, unmatched_count, exposure)

        run.matched_count = matched_count
        run.partially_matched_count = partial_count
        run.flagged_count = flagged_count
        run.unmatched_count = unmatched_count
        run.total_records = int(platform_total) + int(bank_total)
        run.total_monetary_exposure_minor_units = exposure
        run.status = RunStatus.completed
        run.completed_at_utc = datetime.now(timezone.utc)
        run.progress_percent = 100.0
        run.progress_message = "Reconciliation complete"

        await audit_service.log_event(
            db,
            event_type="RECON_RUN_COMPLETED",
            entity_id=run_id,
            entity_type="reconciliation_run",
            actor=run.triggered_by,
            correlation_id=str(uuid.uuid4()),
            after_state={
                "matched": matched_count,
                "flagged": flagged_count,
                "exposure": exposure,
            },
        )
        await db.commit()

        if progress_callback:
            await progress_callback(100, "Reconciliation complete")

        return ReconciliationRunResult(
            matched_count=matched_count,
            unmatched_count=unmatched_count,
            partially_matched_count=partial_count,
            flagged_count=flagged_count,
            total_monetary_exposure=exposure,
        )
