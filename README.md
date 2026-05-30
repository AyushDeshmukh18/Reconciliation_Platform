# Payments Reconciliation Gap Detection Platform

Production-grade platform for ingesting platform transactions and bank settlements, running multi-pass reconciliation, classifying 11 gap types, and providing an analyst workbench.

## Quick Start

### Prerequisites

- Python 3.11
- Node.js 20+
- Ollama (optional): `ollama pull llama3`

### Backend Setup

```bash
cd reconciliation-platform
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Edit .env with your DATABASE_URL and JWT_SECRET_KEY

cd backend
alembic upgrade head
cd ..
python -m backend.db.seed

uvicorn backend.api.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

In a separate terminal — Celery worker (must run from project root, not `backend/`):

```powershell
cd reconciliation-platform
venv\Scripts\activate
pip install -e .   # once — makes `backend` importable everywhere
.\scripts\celery_worker.ps1
```

Or manually:

```powershell
cd reconciliation-platform
$env:PYTHONPATH = (Get-Location).Path
celery -A backend.jobs.celery_app worker --loglevel=info -Q ingestion,reconciliation,reports
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Generate Test Data

```bash
python -m data_generator.generator --seed 42 --mode statistical --year 2024 --month 5 --count 1000 --output ./test_data/
```

### Access

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/api/docs
- Login: `admin` / `admin123` or `analyst` / `analyst123`

## Architecture

- **FastAPI** REST API with JWT auth
- **Celery** background jobs (ingestion, reconciliation, reports)
- **PostgreSQL** (Supabase) with Alembic migrations
- **Multi-pass matcher**: exact → fuzzy → composite
- **Rule engine** with 11 gap classifiers
- **Ollama** integration with circuit breaker and static fallbacks
- **React + TypeScript** premium dark UI

## Gap Types

1. Timing Gap
2. Rounding Difference
3. Duplicate Entry
4. Orphan Refund
5. Partial Settlement
6. Failed Reversal
7. Split Settlement
8. Stale Retry
9. Settlement Truncation
10. Status Mismatch
11. Idempotency Failure
