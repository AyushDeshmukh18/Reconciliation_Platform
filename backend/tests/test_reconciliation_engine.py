import pytest
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
import uuid

from backend.engine.reconciliation_engine import ReconciliationEngine
from backend.api.models.platform_transaction import PlatformTransaction, TransactionStatus
from backend.api.models.bank_settlement import BankSettlement, SettlementStatus
from backend.api.models.reconciliation_run import ReconciliationRun, RunStatus


@pytest.mark.asyncio
async def test_reconciliation_matching(db_session):
    # Insert a test platform tx and a matching bank settlement
    tx = PlatformTransaction(
        transaction_id="tx-test-001",
        merchant_id="M-001",
        amount_minor_units=5000,
        currency_code="INR",
        transaction_status=TransactionStatus.success,
        created_at_utc=datetime.now(timezone.utc) - timedelta(days=2),
        source_file_hash="test-hash",
        raw_record={},
    )
    db_session.add(tx)

    settlement = BankSettlement(
        settlement_id="s-test-001",
        batch_id="B-001",
        transaction_reference="tx-test-001",
        settled_amount_minor_units=5000,
        fee_amount_minor_units=0,
        net_settled_amount_minor_units=5000,
        value_date_utc=datetime.now(timezone.utc) - timedelta(days=1),
        processing_date_utc=datetime.now(timezone.utc),
        settlement_status=SettlementStatus.settled,
        file_hash="test-hash",
        raw_record={},
    )
    db_session.add(settlement)

    await db_session.commit()

    # Create a reconciliation run
    run_id = str(uuid.uuid4())
    run = ReconciliationRun(
        run_id=run_id,
        triggered_by="test",
        started_at_utc=datetime.now(timezone.utc),
        status=RunStatus.queued,
        idempotency_key="test-key",
    )
    db_session.add(run)
    await db_session.commit()

    # Run reconciliation engine
    engine = ReconciliationEngine()

    async def progress_fn(p, msg):
        pass

    result = await engine.run(run_id, db_session, progress_fn)

    # Verify results
    assert result.matched_count == 1
