import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
from sqlalchemy import select

from backend.ingestion.pipeline import ingest_platform_file, ingest_bank_file
from backend.api.models.platform_transaction import PlatformTransaction
from backend.api.models.bank_settlement import BankSettlement


now = datetime.now(timezone.utc)
date1 = (now - timedelta(days=10)).isoformat()
date2 = (now - timedelta(days=5)).isoformat()

SAMPLE_PLATFORM_CSV = f"""transaction_id,merchant_id,amount,currency_code,status,created_at
tx-123,M-456,1000,INR,success,{date1}
tx-456,M-789,2500,INR,failed,{date2}
"""

SAMPLE_BANK_CSV = f"""settlement_id,batch_id,transaction_reference,settled_amount,fee_amount,net_settled_amount,value_date,processing_date,status
s-001,B-001,tx-123,1000,20,1000,{date1},{date2},settled
"""


@pytest.mark.asyncio
async def test_platform_ingestion(db_session):
    content = SAMPLE_PLATFORM_CSV.encode()
    file_hash = hashlib.sha256(content).hexdigest()

    result = await ingest_platform_file(
        content,
        file_hash,
        "test_platform.csv",
        db_session,
        actor="test",
        correlation_id=hashlib.sha256(b"test").hexdigest(),
    )

    assert result.accepted == 2
    assert result.rejected == 0

    txs = (await db_session.execute(select(PlatformTransaction))).scalars().all()
    assert len(txs) == 2
    assert txs[0].merchant_id == "M-456"
    assert txs[0].amount_minor_units == 100000


@pytest.mark.asyncio
async def test_bank_ingestion(db_session):
    content = SAMPLE_BANK_CSV.encode()
    file_hash = hashlib.sha256(content).hexdigest()

    result = await ingest_bank_file(
        content,
        file_hash,
        "test_bank.csv",
        db_session,
        actor="test",
        correlation_id=hashlib.sha256(b"test").hexdigest(),
    )

    assert result.accepted == 1
    assert result.rejected == 0

    settlements = (await db_session.execute(select(BankSettlement))).scalars().all()
    assert len(settlements) == 1
    assert settlements[0].settled_amount_minor_units == 100000


@pytest.mark.asyncio
async def test_platform_ingestion_invalid_data(db_session):
    invalid_content = """transaction_id,merchant_id
tx-123,,
""".encode()
    file_hash = hashlib.sha256(invalid_content).hexdigest()

    result = await ingest_platform_file(
        invalid_content,
        file_hash,
        "invalid.csv",
        db_session,
        actor="test",
        correlation_id=hashlib.sha256(b"test").hexdigest(),
    )

    assert result.accepted == 0
    assert result.rejected >= 1
