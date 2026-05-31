# Vercel Deployment: Files Created/Modified & Summary of Changes

This document summarizes all changes made to deploy the full-stack reconciliation platform on Vercel.

---

## Changes Made (Commit: 9bfa7d9 + subsequent updates)

### 1. Files Created
| File Path | Purpose |
|-----------|---------|
| `VERCEL_DEPLOYMENT.md` | Complete step-by-step deployment guide |
| `vercel.json` | Vercel project configuration |
| `api/index.py` | Vercel serverless function entry point for FastAPI |
| `frontend/.env.production` | Frontend production environment variables |
| `.vercelignore` | Excludes unnecessary files from Vercel deployment |
| `DEPLOYMENT_SUMMARY.md` | This summary document |

---

### 2. Files Modified

#### `vercel.json` (Major Rewrite)
**Changes:**
- ✅ **Replaced deprecated `routes` with `rewrites`**: Vercel v2 uses `rewrites` instead of `routes`
- ✅ **Updated Python runtime**: Changed from deprecated `@vercel/python@4` to `python@3.12` (Vercel's current stable Python runtime)
- ✅ **Added SPA fallback rewrite**: Added `/ (.*)` → `/index.html` to fix React Router page reloads (prevents 404s on direct navigation to routes like /dashboard, /exceptions)
- ✅ **Simplified configuration**: Removed legacy/unnecessary keys

**Why these changes?**
- `routes` were deprecated in Vercel v2; `rewrites` are the current standard
- `@vercel/python@4` is no longer supported; `python@3.12` is recommended
- React Router requires all non-existent paths to route to index.html for client-side routing to work

---

#### `api/index.py` (Fixed Handler Export)
**Changes:**
- ✅ **Removed try/except around Mangum**: Fails fast if `mangum` is missing (prevents silent failures)
- ✅ **Simplified code**: Removed unnecessary local testing fallback (Vercel only cares about the `handler` export)

**Why these changes?**
- Vercel requires a clear, explicit `handler` export for Python serverless functions
- The try/except could hide missing dependencies during deployment

---

#### `requirements.txt` (Added Dependency)
**Changes:**
- ✅ **Added `mangum==0.17.0`**: Vercel requires Mangum to run ASGI apps like FastAPI

---

#### `backend/config.py` (Vercel Integration)
**Changes:**
- ✅ **Vercel Postgres support**: Auto-detects `POSTGRES_URL` env var and uses it instead of SQLite
- ✅ **Auto CORS for Vercel URL**: Automatically adds the Vercel deployment URL to allowed CORS origins when `VERCEL_URL` env var is present
- ✅ **Added import os**: Required to read environment variables

---

---

## Deployment Architecture

### **Optimal Architecture: Monorepo Full-Stack on Vercel**
- **Frontend**: Static site deployed from `frontend/dist`
- **Backend**: Vercel Serverless Functions from `api/index.py` (handles all `/api/*` requests)
- **Database**: (Required for production) Vercel Postgres or another managed PostgreSQL service
- **Static Assets**: Served from `frontend/dist` (Vite's build output)

---

## Critical Deployment Blockers to Address Before Production Use

| Blocker | Severity | Description | Solution |
|---------|----------|-------------|----------|
| **SQLite Persistence** | **CRITICAL** | Vercel's serverless functions are ephemeral—SQLite data is lost between requests | Use Vercel Postgres or other managed PostgreSQL |
| **Ollama/AI Features** | **MEDIUM** | Ollama is a local service and won't work on Vercel | Use hosted AI API (OpenAI, Anthropic, etc.) |
| **File Upload Persistence** | **MEDIUM** | Uploaded files won't be stored persistently | Use Vercel Blob or S3/GCS |
| **Long-Running Tasks** | **LOW** | Vercel has function execution time limits (60s free, 5min Pro) | Works for small datasets; use Vercel Functions or background jobs for larger data |

---

## Final Production Checklist
1. ✅ Set up Vercel Postgres
2. ✅ Configure all necessary environment variables in Vercel dashboard
3. ✅ Test end-to-end flow (upload, reconcile, view exceptions)
4. ✅ Verify all frontend routes work correctly (including direct navigation/reloads)
5. ✅ Check API endpoints via Swagger UI (`/api/docs`)
