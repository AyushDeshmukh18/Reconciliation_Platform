import pytest
from io import BytesIO
from datetime import datetime, timezone
import uuid


@pytest.fixture
def platform_file():
    content = """transaction_id,merchant_id,amount,currency_code,status,created_at
tx-api-001,M-API-001,1000,INR,success,2025-05-20T10:00:00Z
tx-api-002,M-API-002,2000,INR,success,2025-05-21T11:00:00Z
""".encode()
    return BytesIO(content), "test_platform.csv"


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_upload_platform_file(client, platform_file):
    file_data, filename = platform_file
    files = {"file": (filename, file_data, "text/csv")}
    
    response = client.post("/api/v1/reconciliation/ingest/platform", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "queued"


def test_get_platform_transactions(client, db_session, platform_file):
    # First, let's insert some test data directly
    from backend.api.models.platform_transaction import PlatformTransaction, TransactionStatus
    tx1 = PlatformTransaction(
        transaction_id="tx-api-003",
        merchant_id="M-API-003",
        amount_minor_units=1500,
        currency_code="INR",
        transaction_status=TransactionStatus.success,
        created_at_utc=datetime.now(timezone.utc),
        source_file_hash="test-api-hash",
        raw_record={},
    )
    db_session.add(tx1)
    
    response = client.get("/api/v1/transactions/platform?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_reconciliation_run(client):
    response = client.post(
        "/api/v1/reconciliation/runs",
        json={"idempotency_key": f"test-api-key-{uuid.uuid4()}"},
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert "run_id" in data
