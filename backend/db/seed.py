import json
import uuid
import random
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from sqlalchemy import create_engine, select, and_
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
    """Generate realistic amount with Pareto distribution (80/20 principle)"""
    # Pareto distribution for realistic transaction amounts
    alpha = 1.5
    scale = 100  # Minimum amount in minor units
    amount = int(scale * (rng.random() ** (-1/alpha)))
    # Cap maximum amount at 100,000 (1000 units)
    amount = min(amount, 100000)
    # Ensure minimum 100
    amount = max(amount, 100)
    return -amount if is_negative else amount


def generate_merchant_id(rng):
    """Generate realistic merchant IDs"""
    industries = [
        "ECOM", "RETAIL", "FOOD", "TRAVEL", "TECH", "HEALTH",
        "SERVICES", "EDU", "FINTECH", "GAMING", "ENERGY", "AUTOMOTIVE"
    ]
    industry = rng.choice(industries)
    num = rng.randint(1, 750)
    return f"{industry}_{num:03d}"


def generate_currency(rng):
    """Generate realistic currency distribution"""
    return rng.choices(
        ["INR", "USD", "EUR", "GBP", "AUD"],
        weights=[70, 15, 8, 4, 3]
    )[0]


def load_realistic_data():
    import logging
    logger = logging.getLogger(__name__)
    
    settings = get_settings()
    engine = create_engine(settings.DATABASE_SYNC_URL, echo=False)

    # Create tables if they don't exist
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    db = Session()

    rng = random.Random(42)  # Fixed seed for reproducibility

    try:
        logger.info("Seeding database started")
        print("Seeding database started...")

        # -------------------------------
        # Step 1: Create Users (if not exists)
        # -------------------------------
        print("Creating admin/analyst users...")
        existing_users = db.scalar(select(User))
        if not existing_users:
            # Create sample users
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
                User(
                    user_id="550e8400-e29b-41d4-a716-446655440002",
                    username="viewer",
                    email="viewer@reconciliation.io",
                    hashed_password=hash_password("viewer123"),
                    role=UserRole.viewer,
                    is_active=True
                ),
            ]
            db.add_all(users)
            db.commit()
            print("Created default users")

        # -------------------------------
        # Step 2: Create Rule Configs
        # -------------------------------
        print("Creating rule configurations...")
        existing_rules = db.scalar(select(RuleConfig))
        if not existing_rules:
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
                RuleConfig(
                    rule_id="RULE_DUPLICATE_ENTRY",
                    gap_type="duplicate_entry",
                    priority=30,
                    conditions={"amount_match": True, "ref_similar": 0.9},
                    confidence_base=78.0,
                    recommended_action="Investigate duplicate and mark for deletion",
                    description="Similar transaction/settlement already exists",
                    is_active=True,
                    version=1
                ),
                RuleConfig(
                    rule_id="RULE_PARTIAL_SETTLEMENT",
                    gap_type="partial_settlement",
                    priority=40,
                    conditions={"partial_amount": True},
                    confidence_base=88.0,
                    recommended_action="Wait for remaining settlement amount",
                    description="Settlement amount is less than transaction amount",
                    is_active=True,
                    version=1
                ),
                RuleConfig(
                    rule_id="RULE_STATUS_MISMATCH",
                    gap_type="status_mismatch",
                    priority=50,
                    conditions={"status_diff": True},
                    confidence_base=80.0,
                    recommended_action="Verify transaction status with platform",
                    description="Transaction status doesn't match settlement status",
                    is_active=True,
                    version=1
                ),
            ]
            db.add_all(rules)
            db.commit()
            print(f"Created {len(rules)} rule configurations")

        # -------------------------------
        # Step 3: Generate Platform Transactions (5000 records)
        # -------------------------------
        print("Generating platform transactions...")
        platform_transactions = []
        now = datetime.now(timezone.utc)

        for i in range(5000):
            tx_id = str(uuid.uuid4())
            merchant = generate_merchant_id(rng)
            currency = generate_currency(rng)
            
            # Spread transactions over last 120 days
            days_ago = rng.randint(0, 120)
            hours_ago = rng.randint(0, 23)
            minutes_ago = rng.randint(0, 59)
            created_at = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            amount_minor = generate_realistic_amount(rng)
            
            # Some parent transactions (for reversals/refunds)
            parent_tx_id = None
            is_refund = rng.random() < 0.03  # 3% refund rate
            if is_refund and len(platform_transactions) > 50:
                parent_idx = rng.randint(0, len(platform_transactions) - 1)
                parent_tx_id = platform_transactions[parent_idx].transaction_id
                amount_minor = -generate_realistic_amount(rng, is_negative=False)
            
            # Status distribution: recent records should show a visible mix on the frontend
            if days_ago < 30:
                cycle_position = i % 12
                if cycle_position < 5:
                    status = TransactionStatus.success
                elif cycle_position < 8:
                    status = TransactionStatus.pending
                elif cycle_position < 11:
                    status = TransactionStatus.failed
                else:
                    status = TransactionStatus.reversed
            else:
                status_weights = [0.65, 0.18, 0.12, 0.05]  # success, pending, failed, reversed
                status = rng.choices(
                    [TransactionStatus.success, TransactionStatus.pending, TransactionStatus.failed, TransactionStatus.reversed],
                    weights=status_weights
                )[0]

            platform_transactions.append(
                PlatformTransaction(
                    transaction_id=tx_id,
                    merchant_id=merchant,
                    amount_minor_units=amount_minor,
                    currency_code=currency,
                    transaction_status=status,
                    created_at_utc=created_at,
                    idempotency_key=f"idem_{uuid.uuid4().hex[:16]}",
                    parent_transaction_id=parent_tx_id,
                    source_file_hash=f"platform_seed_{days_ago // 14}",
                    raw_record={
                        "id": tx_id,
                        "merchant": merchant,
                        "amount": amount_minor / 100,
                        "currency": currency,
                        "timestamp": created_at.isoformat(),
                        "payment_method": rng.choice(["UPI", "CARD", "NETBANKING", "WALLET"])
                    },
                )
            )
        db.add_all(platform_transactions)
        db.commit()
        print(f"Created {len(platform_transactions)} platform transactions")

        # -------------------------------
        # Step 4: Generate Bank Settlements (~4500 records)
        # -------------------------------
        print("Generating bank settlements...")
        bank_settlements = []
        batch_ids = [f"BATCH_{2024}{m:02d}_{b:03d}" for m in range(1, 13) for b in range(1, 31)]

        settlement_idx = 0
        for platform_tx in platform_transactions:
            if platform_tx.transaction_status not in [TransactionStatus.success, TransactionStatus.pending]:
                continue
            
            # Skip some to create unmatched transactions (~10% unmatched)
            if rng.random() < 0.10:
                continue
            
            value_date = platform_tx.created_at_utc + timedelta(days=rng.choice([1, 2, 3, 4, 5]))
            processing_date = value_date + timedelta(hours=rng.randint(1, 48))
            
            fee_pct = rng.uniform(0.3, 3.5) / 100  # 0.3% to 3.5% fee
            fee_amount = int(abs(platform_tx.amount_minor_units) * fee_pct)
            net_amount = platform_tx.amount_minor_units - fee_amount
            reference = platform_tx.transaction_id
            if rng.random() < 0.18:
                # create a settlement with a variant reference for reconciliation diversity
                reference = rng.choice([
                    f"REF_{platform_tx.transaction_id[:12]}",
                    f"BANK_{rng.randint(100000, 999999)}",
                    f"EXT_{uuid.uuid4().hex[:10]}"
                ])
            if rng.random() < 0.12:
                # partial settlement or duplicate style entries
                partial_factor = rng.choice([0.4, 0.5, 0.75])
                net_amount = int(platform_tx.amount_minor_units * partial_factor) - fee_amount
            settlement = BankSettlement(
                settlement_id=str(uuid.uuid4()),
                batch_id=rng.choice(batch_ids),
                transaction_reference=reference,
                settled_amount_minor_units=platform_tx.amount_minor_units,
                fee_amount_minor_units=fee_amount,
                net_settled_amount_minor_units=net_amount,
                value_date_utc=value_date,
                processing_date_utc=processing_date,
                settlement_status=rng.choices(
                    [SettlementStatus.settled, SettlementStatus.held, SettlementStatus.reversed, SettlementStatus.returned],
                    weights=[0.84, 0.08, 0.05, 0.03]
                )[0],
                file_hash=f"bank_seed_{value_date.date().isoformat()}",
                batch_sequence_number=settlement_idx,
                raw_record={
                    "settlement_id": str(uuid.uuid4()),
                    "batch": rng.choice(batch_ids),
                    "ref": reference,
                    "amount": platform_tx.amount_minor_units / 100,
                    "fee": fee_amount / 100,
                    "net": net_amount / 100,
                    "bank": rng.choice(["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "YES_BANK", "BOB"])
                },
            )
            bank_settlements.append(settlement)
            settlement_idx += 1

        # Add some bank-only settlement entries to increase unmatched bank-side volume
        for _ in range(int(len(platform_transactions) * 0.05)):
            orphan_amount = generate_realistic_amount(rng)
            batch_date = now - timedelta(days=rng.randint(0, 120))
            bank_settlements.append(
                BankSettlement(
                    settlement_id=str(uuid.uuid4()),
                    batch_id=rng.choice(batch_ids),
                    transaction_reference=f"BANK_ORPHAN_{uuid.uuid4().hex[:10]}",
                    settled_amount_minor_units=orphan_amount,
                    fee_amount_minor_units=int(abs(orphan_amount) * rng.uniform(0.004, 0.025)),
                    net_settled_amount_minor_units=orphan_amount,
                    value_date_utc=batch_date,
                    processing_date_utc=batch_date + timedelta(hours=rng.randint(1, 72)),
                    settlement_status=rng.choices(
                        [SettlementStatus.settled, SettlementStatus.held, SettlementStatus.returned],
                        weights=[0.7, 0.2, 0.1]
                    )[0],
                    file_hash=f"bank_orphan_{batch_date.date().isoformat()}",
                    batch_sequence_number=settlement_idx,
                    raw_record={
                        "settlement_id": str(uuid.uuid4()),
                        "batch": rng.choice(batch_ids),
                        "ref": f"BANK_ORPHAN_{uuid.uuid4().hex[:10]}",
                        "amount": orphan_amount / 100,
                        "fee": 0,
                        "net": orphan_amount / 100,
                        "bank": rng.choice(["HDFC", "ICICI", "SBI", "AXIS", "KOTAK", "YES_BANK", "BOB"])
                    },
                )
            )
            settlement_idx += 1

        db.add_all(bank_settlements)
        db.commit()
        print(f"Created {len(bank_settlements)} bank settlements")

        # -------------------------------
        # Step 5: Generate Reconciliation Runs (daily for last 60 days)
        # -------------------------------
        print("Generating reconciliation runs...")
        recon_runs = []
        user_ids = ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]

        for i in range(60):
            run_started = now - timedelta(days=(60 - i))
            run_completed = run_started + timedelta(minutes=rng.randint(5, 45))
            
            # Vary counts over time
            total = len(platform_transactions) + len(bank_settlements)
            matched = int(total * max(0.70, 0.82 - i * 0.002))
            unmatched = int(total * min(0.18, 0.08 + i * 0.0015))
            partially_matched = int(total * min(0.07, 0.04 + i * 0.0007))
            flagged = int(total * min(0.10, 0.06 + i * 0.0009))
            exposure = 800000 + i * 62000
            
            recon_runs.append(
                ReconciliationRun(
                    run_id=str(uuid.uuid4()),
                    triggered_by=rng.choice(user_ids),
                    started_at_utc=run_started,
                    completed_at_utc=run_completed,
                    status=RunStatus.completed if i < 59 else RunStatus.running,
                    total_records=total,
                    matched_count=max(matched, 1000),
                    unmatched_count=max(unmatched, 100),
                    partially_matched_count=max(partially_matched, 50),
                    flagged_count=max(flagged, 30),
                    total_monetary_exposure_minor_units=exposure,
                    idempotency_key=f"recon_idemp_{i:03d}",
                )
            )

        db.add_all(recon_runs)
        db.commit()
        print(f"Created {len(recon_runs)} reconciliation runs")

        # -------------------------------
        # Step 6: Generate Reconciliation Results (~4000 records)
        # -------------------------------
        print("Generating reconciliation results...")
        recon_results = []
        last_run = recon_runs[-1]
        last_run_id = last_run.run_id

        max_idx = min(len(platform_transactions), len(bank_settlements), 4000)
        
        for i in range(max_idx):
            platform = platform_transactions[i]
            bank = bank_settlements[i] if i < len(bank_settlements) else None

            match_type = MatchType.exact
            gap_type = GapType.unclassified
            recon_status = ReconStatus.matched
            confidence = 99.0
            monetary_diff = 0
            requires_review = False
            
            # Status distribution: balanced flagged/partial/unmatched exception categories
            gap_cycle = [
                GapType.rounding_difference,
                GapType.partial_settlement,
                GapType.status_mismatch,
                GapType.split_settlement,
                GapType.timing_gap,
                GapType.duplicate_entry,
                GapType.orphan_refund,
                GapType.idempotency_failure,
                GapType.settlement_truncation,
                GapType.failed_reversal,
            ]

            rand_val = rng.random()
            if rand_val < 0.45:
                recon_status = ReconStatus.matched
                match_type = MatchType.exact
                gap_type = GapType.unclassified
                confidence = rng.uniform(95, 99.9)
                monetary_diff = 0
            elif rand_val < 0.70:
                recon_status = ReconStatus.flagged
                match_type = rng.choice([MatchType.fuzzy, MatchType.composite])
                gap_type = gap_cycle[i % len(gap_cycle)]
                confidence = rng.uniform(58, 86)
                base = abs(platform.amount_minor_units) if platform.amount_minor_units else 1000
                monetary_diff = int(base * rng.choice([0.01, 0.02, 0.03, 0.05, -0.01, -0.02, -0.03]))
                requires_review = confidence < 80
            elif rand_val < 0.90:
                recon_status = ReconStatus.partially_matched
                match_type = MatchType.partial
                gap_type = [
                    GapType.partial_settlement,
                    GapType.split_settlement,
                    GapType.status_mismatch,
                    GapType.timing_gap,
                ][i % 4]
                confidence = rng.uniform(64, 91)
                monetary_diff = int(platform.amount_minor_units * rng.choice([0.20, 0.35, -0.20, -0.35]))
                requires_review = confidence < 82
            else:
                recon_status = ReconStatus.flagged
                match_type = MatchType.unmatched
                gap_type = [
                    GapType.orphan_refund,
                    GapType.idempotency_failure,
                    GapType.settlement_truncation,
                    GapType.failed_reversal,
                    GapType.stale_retry,
                ][i % 5]
                confidence = rng.uniform(50, 82)
                monetary_diff = int(platform.amount_minor_units * rng.choice([0.25, 0.5, 1.0, -0.5, -1.0]))
                requires_review = True
            
            # Provide human-friendly explanations and suggestions to make exceptions realistic
            explanation_templates = {
                GapType.rounding_difference: "Monetary difference consistent with expected rounding on currency conversion.",
                GapType.partial_settlement: "Settlement amount is smaller than transaction amount; likely partial settlement.",
                GapType.status_mismatch: "Platform status and settlement status differ; investigate reversal/chargeback.",
                GapType.split_settlement: "Transaction split across multiple settlement records.",
                GapType.timing_gap: "Settlement occurred outside expected window; timing mismatch.",
                GapType.duplicate_entry: "Duplicate transaction or settlement detected.",
                GapType.orphan_refund: "Refund present without matching original transaction.",
                GapType.idempotency_failure: "Idempotency key indicates multiple submissions.",
                GapType.settlement_truncation: "Settlement file truncation or formatting issue detected.",
                GapType.failed_reversal: "Reversal attempted but not reflected in settlement.",
                GapType.unclassified: "Requires manual review to determine root cause.",
            }

            suggestion_templates = [
                "Contact bank to obtain settlement batch details and confirm amounts.",
                "Review merchant records and reconcile against payment gateway logs.",
                "Accept as rounding difference if within configured tolerance and close.",
                "Split amounts indicate partial settlement — await subsequent batch.",
                "Flag for manual review and attach supporting evidence.",
            ]

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
                    rule_id_fired=(f"RULE_{gap_type.value.upper()}" if recon_status != ReconStatus.matched else None),
                    rule_evaluation_trace=[
                        {
                            "rule_id": "RULE_EXACT_MATCH",
                            "gap_type": "unclassified",
                            "conditions_tested": {
                                "amount_match": bank is not None and platform.amount_minor_units == bank.settled_amount_minor_units,
                                "ref_match": bank is not None and platform.transaction_id == bank.transaction_reference,
                            },
                            "fired": recon_status == ReconStatus.matched,
                            "confidence": float(confidence if recon_status == ReconStatus.matched else min(confidence + 5, 95))
                        },
                        {
                            "rule_id": "RULE_FUZZY_MATCH",
                            "gap_type": gap_type.value,
                            "conditions_tested": {
                                "merchant_similar": True,
                                "amount_within_tolerance": abs(monetary_diff) <= abs(platform.amount_minor_units) * 0.05,
                            },
                            "fired": match_type == MatchType.fuzzy or match_type == MatchType.composite,
                            "confidence": float(confidence)
                        },
                        {
                            "rule_id": "RULE_REVIEW_REQUIRED",
                            "gap_type": gap_type.value,
                            "conditions_tested": {
                                "status_diff": bank is not None and bank.settlement_status != SettlementStatus.settled,
                            },
                            "fired": requires_review,
                            "confidence": float(confidence - 10 if requires_review else confidence)
                        }
                    ],
                    gap_explanation=explanation_templates.get(gap_type, ""),
                    resolution_suggestion=rng.choice(suggestion_templates),
                    requires_secondary_review=requires_review,
                )
            )

        db.add_all(recon_results)
        db.commit()
        print(f"Created {len(recon_results)} reconciliation results")

        # -------------------------------
        # Step 7: Generate Resolution Notes (~600 notes)
        # -------------------------------
        print("Generating resolution notes...")
        resolution_notes = []
        analyst_user_ids = ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
        
        note_templates = [
            "Reviewed transaction, appears to be a {gap_type}. Will follow up with bank.",
            "Confirmed with merchant - this is a legitimate {gap_type}. No action needed.",
            "AI suggests this is a {gap_type}. Manual review pending.",
            "Investigating {gap_type} - contacting finance team for clarification.",
            "Resolved {gap_type} - matched to transaction from previous batch.",
            "Marked {gap_type} as acceptable - within tolerance thresholds.",
        ]

        flagged_results = [r for r in recon_results if r.recon_status == ReconStatus.flagged][:600]
        for result in flagged_results:
            is_ai_suggested = rng.random() < 0.25
            note_text = rng.choice(note_templates).format(gap_type=result.gap_type.value.replace("_", " "))
            
            resolution_notes.append(
                ResolutionNote(
                    note_id=str(uuid.uuid4()),
                    result_id=result.result_id,
                    analyst_id=rng.choice(analyst_user_ids),
                    note_text=note_text,
                    is_ai_suggested=is_ai_suggested,
                )
            )

        db.add_all(resolution_notes)
        db.commit()
        print(f"Created {len(resolution_notes)} resolution notes")

        # -------------------------------
        # Step 8: Generate Audit Logs (~1000 entries)
        # -------------------------------
        print("Generating audit logs...")
        audit_logs = []
        
        event_types = [
            "USER_LOGIN", "FILE_UPLOAD", "RECONCILIATION_START", "RECONCILIATION_COMPLETE",
            "EXCEPTION_ASSIGN", "EXCEPTION_RESOLVE", "NOTE_ADD", "RULE_UPDATE",
            "USER_CREATE", "SETTINGS_CHANGE", "REPORT_GENERATE"
        ]
        
        entity_types = ["user", "file", "reconciliation_run", "exception", "note", "rule", "report"]
        actors = ["admin", "analyst", "system", "550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"]
        
        for i in range(1000):
            log_time = now - timedelta(
                days=rng.randint(0, 120),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59)
            )
            
            audit_logs.append(
                AuditLog(
                    event_id=str(uuid.uuid4()),
                    event_type=rng.choice(event_types),
                    entity_type=rng.choice(entity_types),
                    entity_id=str(uuid.uuid4()),
                    actor=rng.choice(actors),
                    before_state=None if rng.random() < 0.3 else {"old_val": rng.randint(1, 100)},
                    after_state={"new_val": rng.randint(1, 100)},
                    created_at_utc=log_time,
                    correlation_id=str(uuid.uuid4()),
                    file_hash=f"audit_{i:04d}" if rng.random() < 0.2 else None,
                )
            )
        
        db.add_all(audit_logs)
        db.commit()
        print(f"Created {len(audit_logs)} audit logs")

        # -------------------------------
        # Final Audit log for seed completion
        # -------------------------------
        audit_entry = AuditLog(
            event_id=str(uuid.uuid4()),
            event_type="SEED_DATA_LOADED",
            entity_type="system",
            entity_id=str(uuid.uuid4()),
            actor="system",
            before_state=None,
            after_state={
                "platform_transactions": len(platform_transactions),
                "bank_settlements": len(bank_settlements),
                "reconciliation_runs": len(recon_runs),
                "reconciliation_results": len(recon_results),
                "resolution_notes": len(resolution_notes),
                "audit_logs": len(audit_logs),
            },
            correlation_id=str(uuid.uuid4()),
        )
        db.add(audit_entry)
        db.commit()

        logger.info("Seeding completed successfully")
        print("\n" + "="*60)
        print("SEED DATA LOAD COMPLETE!")
        print("="*60)
        print(f"Platform Transactions: {len(platform_transactions):,}")
        print(f"Bank Settlements:      {len(bank_settlements):,}")
        print(f"Reconciliation Runs:   {len(recon_runs):,}")
        print(f"Reconciliation Results:{len(recon_results):,}")
        print(f"Resolution Notes:      {len(resolution_notes):,}")
        print(f"Audit Logs:            {len(audit_logs):,}")
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
