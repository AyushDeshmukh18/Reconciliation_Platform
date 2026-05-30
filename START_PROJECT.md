# Start the Reconciliation Platform (End-to-End)

This document provides step-by-step commands to start the repository end-to-end (backend API, worker, and frontend), with both PowerShell (Windows) and Bash examples. It assumes you have Python 3.11, Node.js/npm, and optional Redis installed.

## 1) Environment
- Python: 3.11
- Node.js + npm
- Optional: Redis (for Celery), or use the local task runner fallback

## 2) Create and activate Python virtual environment (PowerShell)
```powershell
cd "d:\VS Codes\Reconciliation platform\reconciliation-platform"
python -m venv .\venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 2b) (Bash / WSL / macOS / Linux)
```bash
cd "d:/VS Codes/Reconciliation platform/reconciliation-platform"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 3) Database setup and seed (SQLite default)
```powershell
# From project root (PowerShell)
cd "d:\VS Codes\Reconciliation platform\reconciliation-platform"
# This script drops, recreates, and seeds the DB
python reset_and_reseed.py
```

## 4) Run backend API (development)
```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1
# Start uvicorn with reload
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```
Bash equivalent:
```bash
source venv/bin/activate
uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
```

- API will be available at: `http://127.0.0.1:8000`
- Open docs at: `http://127.0.0.1:8000/docs`

## 5) Background worker (Celery) — optional
- If you have Redis running (default Celery broker), start Redis first.

PowerShell:
```powershell
# Start Redis separately (if installed)
# Start Celery worker from project root
.\venv\Scripts\Activate.ps1
celery -A backend.jobs.local_tasks worker --loglevel=info
```

Bash:
```bash
source venv/bin/activate
celery -A backend.jobs.local_tasks worker --loglevel=info
```

- If you do not have Redis, the project includes a local task fallback; no worker is required for local runs.

## 6) Frontend (dev server)
PowerShell:
```powershell
cd frontend
npm install
npm run dev
```
Bash:
```bash
cd frontend
npm install
npm run dev
```

- Frontend dev server typically runs at `http://localhost:5173` (Vite default).

## 7) Build frontend for production
PowerShell:
```powershell
cd frontend
npm run build
```

## 8) Running end-to-end tests (Playwright)
```powershell
# Ensure frontend dev server and backend are running
# From workspace root
npm --prefix frontend run build
pytest -q
```

## 9) Troubleshooting
- Virtual environment issues: ensure `python` resolves to 3.11. Use the full path if needed.
- SQLite DB file: by default `app.db` is created in project root under backend (check `DATABASE_URL` in `backend/config.py`).
- Celery/Redis: if Celery cannot connect, confirm `CELERY_BROKER_URL` in environment; otherwise local fallback will be used.
- Ports conflicts: change `uvicorn` or Vite port via CLI options.

## 10) Quick one-liners
Start backend + frontend (PowerShell):
```powershell
# Backend (in one tab)
.\venv\Scripts\Activate.ps1; uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
# Frontend (in another tab)
cd frontend; npm run dev
```

Start backend + Celery worker (PowerShell):
```powershell
.\venv\Scripts\Activate.ps1; uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
.\venv\Scripts\Activate.ps1; celery -A backend.jobs.local_tasks worker --loglevel=info
```

If you'd like, I can add environment variable examples, Docker compose files, or CI scripts next.
