# Vercel Deployment Guide: Frontend + Backend (Same Project)

This guide explains how to deploy the entire Payments Reconciliation Gap Detection Platform (frontend + backend) to Vercel in a single project.

---

## Prerequisites
1. Vercel account (free tier works)
2. GitHub/GitLab/Bitbucket repository with the project
3. Basic knowledge of Vercel

---

## Step 1: Project Structure for Vercel
Your project should have this structure (we've created/modified all necessary files):
```
reconciliation-platform/
├── api/                    # Vercel serverless functions (backend)
│   └── index.py           # FastAPI entry point (Mangum handler)
├── backend/                # Original backend code
├── frontend/               # Original frontend code
├── runtime.txt             # Specifies Python version for Vercel
├── vercel.json             # Vercel configuration
├── requirements.txt        # Python dependencies
├── package.json            # Frontend dependencies (in frontend/)
└── ... (other files)
```

---

## Step 2: Key Configuration (Already Applied)

### 2.1 Runtime Configuration (`runtime.txt`)
- **Critical**: Vercel was using Python 3.14 which is incompatible with our dependencies
- **Fixed**: Pinned to `python-3.12.10` (stable, compatible with FastAPI 0.111, Pydantic 2.7.x, SQLAlchemy 2.0.x, Pandas 2.2.x)

### 2.2 Vercel Configuration (`vercel.json`)
- Uses `python@3.12` runtime (deprecated `@vercel/python@4` removed)
- Uses `rewrites` (deprecated `routes` removed)
- SPA fallback for React Router
- Correct build commands and output directories
- API rewrite: `/api/*` → `/api/index.py`

### 2.3 Backend Entry Point (`api/index.py`)
- Proper Mangum handler export
- No try/except around Mangum (fails fast if dependencies missing)

### 2.4 Backend Config (`backend/config.py`)
- Auto-detects Vercel environment (via `APP_ENV=production` or `VERCEL` env var)
- **Important**: Vercel Serverless Functions only allow writing to `/tmp`! So all paths are updated:
  - Database: `/tmp/app.db`
  - Reports: `/tmp/reports`
  - Uploads: `/tmp/uploads`
- Auto-adds Vercel's deployment URL to CORS origins

### 2.5 Frontend Environment
- Frontend uses relative API paths (works with Vercel's proxy)
- Environment variables configured in Vercel dashboard

---

## Step 3: Vercel Project Setup

1. Go to [vercel.com](https://vercel.com) and log in
2. Click "Add New Project"
3. Import your GitHub/GitLab/Bitbucket repository (`https://github.com/AyushDeshmukh18/Reconciliation_Platform.git`)
4. **Configure Project**:
   - **Framework Preset**: Select "Vite" (auto-detected)
   - **Root Directory**: Leave empty (repo root)
   - **Build Command**: (auto-detected as `cd frontend && npm run build`)
   - **Output Directory**: (auto-detected as `frontend/dist`)
   - **Install Command**: (auto-detected as)
5. **Environment Variables (Required)**:
   Add these **Production Environment Variables** in Vercel Dashboard → Project Settings → Environment Variables:
   ```
   DATABASE_URL=sqlite+aiosqlite:///tmp/app.db
   DATABASE_SYNC_URL=sqlite:////tmp/app.db
   APP_ENV=production
   REPORTS_DIR=/tmp/reports
   UPLOADS_DIR=/tmp/uploads
   DEFAULT_CURRENCY=INR
   ```
   (Note: You can leave out the database ones since config.py will auto-set them, but adding them explicitly is okay)
6. Click "Deploy"

---

## Step 4: Deployment Considerations

### ⚠️ **Major Deployment Notes**

#### 1. **SQLite Persistence (Important)**
- **Vercel Limitation**: Serverless functions are ephemeral—SQLite data in `/tmp` is NOT persisted between function invocations!
- **What this means**: Every time a new serverless function spins up, it gets a fresh empty database
- **For Real Production Use**: Replace with **Vercel Postgres** (recommended), Supabase, Neon, or another managed database
- **For testing**: This SQLite setup works for trying out the app

#### 2. **Ollama/AI Features**
- **Problem**: Ollama is a local model server and will not work on Vercel
- **Solution**: For AI features in production, use a hosted AI service (OpenAI API, Anthropic API, etc.)
- **Current Impact**: The `ollama_service.py` will fail gracefully, but AI-generated explanations won't work

#### 3. **Long-Running Tasks**
- **Problem**: Vercel serverless functions have a maximum execution time (60s for free tier, up to 5min for Pro)
- **Current Mitigation**: Backend uses local background tasks that work within these limits for small datasets

#### 4. **File Upload Persistence**
- **Problem**: Files uploaded to `/tmp/uploads` are not persisted between invocations
- **Solution**: Use Vercel Blob Storage or another cloud storage service (S3, GCS, etc.) for real production use

---

## Step 5: Testing the Deployment
1. Open your Vercel deployment URL (e.g., `https://your-app.vercel.app`)
2. Test all frontend pages (Dashboard, Upload Center, Exceptions, etc.)
3. Test the backend API:
   - Health check: `https://your-app.vercel.app/api/health` → Should return `{"status":"ok"}`
   - API docs: `https://your-app.vercel.app/api/docs` (Swagger UI should load)

---

## Step 6: Optional: CLI Deployment
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy to preview: `vercel`
4. Deploy to production: `vercel --prod`
