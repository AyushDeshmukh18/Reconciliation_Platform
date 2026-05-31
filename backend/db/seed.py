import json
import uuid
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.api.models.audit_log import AuditLog
from backend.api.models.bank_settlement import BankSettlement, SettlementStatus
from backend.api.models.platform_transaction import PlatformTransaction, TransactionStatus
from backend.api.models.reconciliation_result import (
    ReconciliationResult,
    MatchType,
    GapType,
    ReconStatus,
)
from backend.api.models.reconciliation_run import ReconciliationRun, RunStatus
from backend.api.models.resolution_note import ResolutionNote
from backend.api.models.user import User, UserRole
from backend.api.models.rule_config import RuleConfig
from backend.config import get_settings
from backend.db.base import Base


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def generate_realistic_amount(rng, is_negative=False):
    alpha = 1.5
    scale = 100
    amount = int(scale * (rng.random() ** (-1/alpha)))
    amount = min(amount, 100000)
    amount = max(amount, 100)
    return -amount if is_negative else amount


def generate_merchant_id(rng):
    industries = [
        "ECOM", "RETAIL", "FOOD", "TRAVEL", "TECH", "HEALTH",
        "SERVICES", "EDU", "FINTECH"
    ]
    industry = rng.choice(industries)
    num = rng.randint(1, 100)
    return f"{industry}_{num:03d}"


def generate_currency(rng):
    return rng.choices(
        ["INR", "USD", "EUR", "GBP"],
        weights=[70, 15, 10, 5]
    )[0]


def load_realistic_data():
    import logging
    logger = logging.getLogger(__name__)
    
    settings = get_settings()
    engine = create_engine(settings.DATABASE_SYNC_URL, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    rng = random.Random(42)

    try:
        # Check if ANY data exists (idempotent)
        has_data = False
        tables = [User, RuleConfig, PlatformTransaction, BankSettlement, ReconciliationRun, ReconciliationResult]
        for table in tables:
            if db.scalar(select(table)):
                has_data = True
                break
        
        if has_data:
            logger.info("Database already has data, skipping seed")
            print("Database already has data, skipping seed")
            return

        logger.info("Seeding database started")
        print("Seeding database started...")

        # Collect ALL objects first, commit once at end!
        all_objects = []

        # -------------------------------
        # Step 1: Create Users
        # -------------------------------
        users = [
            User(
                user_id="550e8400-e29b-41d4-a716-446655440000",
                username="admin",
                email="admin@reconciliation.io",
                hashed_password=hash_password("admin123"),
                role=UserRole.admin,
                is_active=True
            ),
            User(
                user_id="550e8400-e29b-41d4-a716-446655440001",
                username="analyst",
                email="analyst@reconciliation.io",
                hashed_password=hash_password("analyst123"),
                role=UserRole.analyst,
                is_active=True
            ),
        ]
        all_objects.extend(users)

        # -------------------------------
        # Step 2: Create Rule Configs
        # -------------------------------
        rules = [
            RuleConfig(
                rule_id="RULE_TIMING_GAP",
                gap_type="timing_gap",
                priority=10,
                conditions={"time_diff_min": 1, "time_diff_max": 7},
                confidence_base=85.0,
                recommended_action="Check settlement timing and confirm with bank",
                description="Transaction and settlement dates differ by 1-7 days",
                is_active=True,
                version=1
            ),
            RuleConfig(
                rule_id="RULE_ROUNDING_DIFF",
                gap_type="rounding_difference",
                priority=20,
                conditions={"max_diff": 5},
                confidence_base=92.0,
                recommended_action="Accept rounding difference and close",
                description="Monetary difference <= 5 minor units (rounding error)",
                is_active=True,
                version=1
            ),
        ]
        all_objects.extend(rules)

        # -------------------------------
        # Step 3: Generate Platform Transactions (100 records total)
        # -------------------------------
        platform_transactions = []
        now = datetime.now(timezone.utc)

        for i in range(100):
            tx_id = str(uuid.uuid4())
            merchant = generate_merchant_id(rng)
            currency = generate_currency(rng)
            days_ago = rng.randint(0, 30)
            created_at = now - timedelta(days=days_ago)
            amount_minor = generate_realistic_amount(rng)
            
            if days_ago < 10:
                cycle_position = i % 4
                if cycle_position < 2:
                    status = TransactionStatus.success
                elif cycle_position < 3:
                    status = TransactionStatus.pending
                else:
                    status = TransactionStatus.failed
            else:
                status = TransactionStatus.success

            platform_transactions.append(
                PlatformTransaction(
                    transaction_id=tx_id,
                    merchant_id=merchant,
                    amount_minor_units=amount_minor,
                    currency_code=currency,
                    transaction_status=status,
                    created_at_utc=created_at,
                    idempotency_key=f"idem_{uuid.uuid4().hex[:10]}",
                    source_file_hash="platform_seed",
                    raw_record={
                        "id": tx_id,
                        "merchant": merchant,
                        "amount": amount_minor / 100,
                        "currency": currency,
                        "timestamp": created_at.isoformat(),
                        "payment_method": rng.choice(["UPI", "CARD", "NETBANKING"])
                    },
                )
            )
        all_objects.extend(platform_transactions)

        # -------------------------------
        # Step 4: Generate Bank Settlements (~90 records)
        # -------------------------------
        bank_settlements = []
        batch_ids = [f"BATCH_202406_{i:03d}" for i in range(1, 31)]
        settlement_idx = 0

        for platform_tx in platform_transactions:
            if platform_tx.transaction_status not in [TransactionStatus.success, TransactionStatus.pending]:
                continue
            
            if rng.random() < 0.10:
                continue
            
            value_date = platform_tx.created_at_utc + timedelta(days=rng.choice([1, 2]))
            processing_date = value_date + timedelta(hours=rng.randint(1, 24))
            fee_pct = rng.uniform(0.3, 2.0) / 100
            fee_amount = int(abs(platform_tx.amount_minor_units) * fee_pct)
            net_amount = platform_tx.amount_minor_units - fee_amount
            reference = platform_tx.transaction_id

            settlement = BankSettlement(
                settlement_id=str(uuid.uuid4()),
                batch_id=rng.choice(batch_ids),
                transaction_reference=reference,
                settled_amount_minor_units=platform_tx.amount_minor_units,
                fee_amount_minor_units=fee_amount,
                net_settled_amount_minor_units=net_amount,
                value_date_utc=value_date,
                processing_date_utc=processing_date,
                settlement_status=SettlementStatus.settled,
                file_hash="bank_seed",
                batch_sequence_number=settlement_idx,
                raw_record={
                    "settlement_id": str(uuid.uuid4()),
                    "batch": rng.choice(batch_ids),
                    "ref": reference,
                    "amount": platform_tx.amount_minor_units / 100,
                    "fee": fee_amount / 100,
                    "net": net_amount / 100,
                    "bank": rng.choice(["HDFC", "ICICI", "SBI", "AXIS"])
                },
            )
            bank_settlements.append(settlement)
            settlement_idx += 1
        all_objects.extend(bank_settlements)

        # -------------------------------
        # Step 5: Generate Reconciliation Runs (3 days only)
        # -------------------------------
        recon_runs = []
        user_ids = [u.user_id for u in users]

        for i in range(3):
            run_started = now - timedelta(days=(2 - i))
            run_completed = run_started + timedelta(minutes=rng.randint(5, 15))
            total = len(platform_transactions) + len(bank_settlements)
            matched = int(total * 0.75)
            unmatched = int(total * 0.15)
            partially_matched = int(total * 0.05)
            flagged = int(total * 0.05)
            exposure = 800000
            
            recon_runs.append(
                ReconciliationRun(
                    run_id=str(uuid.uuid4()),
                    triggered_by=rng.choice(user_ids),
                    started_at_utc=run_started,
                    completed_at_utc=run_completed,
                    status=RunStatus.completed,
                    total_records=total,
                    matched_count=matched,
                    unmatched_count=unmatched,
                    partially_matched_count=partially_matched,
                    flagged_count=flagged,
                    total_monetary_exposure_minor_units=exposure,
                    idempotency_key=f"recon_idemp_{i:02d}",
                )
            )
        all_objects.extend(recon_runs)

        # -------------------------------
        # Step 6: Generate Reconciliation Results (~80 records)
        # -------------------------------
        recon_results = []
        last_run = recon_runs[-1]
        last_run_id = last_run.run_id
        max_idx = min(len(platform_transactions), len(bank_settlements), 80)

        for i in range(max_idx):
            platform = platform_transactions[i]
            bank = bank_settlements[i] if i < len(bank_settlements) else None

            match_type = MatchType.exact
            gap_type = GapType.unclassified
            recon_status = ReconStatus.matched
            confidence = 99.0
            monetary_diff = 0
            requires_review = False

            rand_val = rng.random()
            if rand_val < 0.70:
                recon_status = ReconStatus.matched
            elif rand_val < 0.85:
                recon_status = ReconStatus.flagged
                match_type = MatchType.fuzzy
                gap_type = GapType.rounding_difference
                confidence = rng.uniform(70, 85)
                monetary_diff = int(abs(platform.amount_minor_units) * 0.02)
                requires_review = True
            elif rand_val < 0.95:
                recon_status = ReconStatus.partially_matched
                match_type = MatchType.partial
                gap_type = GapType.partial_settlement
                confidence = rng.uniform(75, 90)
                requires_review = True
            else:
                recon_status = ReconStatus.unmatched
                match_type = MatchType.unmatched
                gap_type = GapType.orphan_refund
                requires_review = True

            recon_results.append(
                ReconciliationResult(
                    result_id=str(uuid.uuid4()),
                    run_id=last_run_id,
                    platform_transaction_id=platform.transaction_id,
                    bank_settlement_id=bank.settlement_id if bank else None,
                    match_type=match_type,
                    gap_type=gap_type,
                    gap_confidence=confidence,
                    monetary_difference_minor_units=monetary_diff,
                    recon_status=recon_status,
                    requires_secondary_review=requires_review,
                )
            )
        all_objects.extend(recon_results)

        # -------------------------------
        # Step 7: Generate Resolution Notes (20 notes)
        # -------------------------------
        resolution_notes = []
        flagged_results = [r for r in recon_results if r.recon_status in [ReconStatus.flagged, ReconStatus.unmatched]][:20]
        for result in flagged_results:
            resolution_notes.append(
                ResolutionNote(
                    note_id=str(uuid.uuid4()),
                    result_id=result.result_id,
                    analyst_id=users[1].user_id,
                    note_text="Manual review pending",
                    is_ai_suggested=rng.random() < 0.3,
                )
            )
        all_objects.extend(resolution_notes)

        # -------------------------------
        # Final Audit log for seed completion
        # -------------------------------
        audit_entry = AuditLog(
            event_id=str(uuid.uuid4()),
            event_type="SEED_DATA_LOADED",
            entity_type="system",
            entity_id=str(uuid.uuid4()),
            actor="system",
            after_state={
                "platform_transactions": len(platform_transactions),
                "bank_settlements": len(bank_settlements),
                "reconciliation_runs": len(recon_runs),
                "reconciliation_results": len(recon_results),
                "resolution_notes": len(resolution_notes),
            },
            correlation_id=str(uuid.uuid4()),
        )
        all_objects.append(audit_entry)

        # -------------------------------
        # COMMIT ALL AT ONCE!
        # -------------------------------
        db.add_all(all_objects)
        db.commit()
        logger.info("Seeding completed successfully")
        print("\n" + "="*60)
        print("SEED DATA LOAD COMPLETE!")
        print("="*60)
        print(f"Platform Transactions: {len(platform_transactions)}")
        print(f"Bank Settlements:      {len(bank_settlements)}")
        print(f"Reconciliation Runs:   {len(recon_runs)}")
        print(f"Reconciliation Results:{len(recon_results)}")
        print(f"Resolution Notes:      {len(resolution_notes)}")
        print("="*60)

    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_realistic_data()
