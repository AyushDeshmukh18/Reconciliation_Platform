# Vercel Deployment Guide: Frontend + Backend (Same Project)

This guide explains how to deploy the entire Payments Reconciliation Gap Detection Platform (frontend + backend) to Vercel in a single project.

## Prerequisites
1. Vercel account (free tier works)
2. GitHub/GitLab/Bitbucket repository with the project
3. Basic knowledge of Vercel

---

## Step 1: Project Structure for Vercel
Your project should have this structure (we'll create missing files):
```
reconciliation-platform/
├── api/                    # Vercel serverless functions (backend)
│   └── index.py           # FastAPI entry point
├── backend/                # Original backend code
├── frontend/               # Original frontend code
├── vercel.json             # Vercel configuration
├── requirements.txt        # Python dependencies
├── package.json            # Frontend dependencies (in frontend/)
└── ... (other files)
```

---

## Step 2: Create Required Configuration Files

### 2.1 Create `vercel.json`
This configures Vercel to handle both frontend and backend routes.

### 2.2 Create `api/index.py`
Vercel serverless function entry point for FastAPI.

### 2.3 Update `backend/config.py`
Make backend compatible with Vercel environment variables.

### 2.4 Update `frontend/vite.config.ts`
Set correct base path and build output directory.

### 2.5 Create `.vercelignore`
Exclude unnecessary files from deployment.

---

## Step 3: Vercel Project Setup
1. Go to [vercel.com](https://vercel.com) and log in
2. Click "Add New Project"
3. Import your GitHub/GitLab/Bitbucket repository
4. **Configure Project**:
   - **Framework Preset**: Select "Vite"
   - **Root Directory**: Leave empty (or set to `reconciliation-platform` if repo has nested folder)
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `cd frontend && npm install`
5. **Environment Variables**:
   - Add any required env vars (see `backend/config.py` and `frontend/.env`)
   - For SQLite: Vercel's serverless functions are ephemeral, so SQLite won't work persistently. For production, use a managed PostgreSQL database (e.g., Supabase, Vercel Postgres)
6. Click "Deploy"

---

## Step 4: Deploying
1. Vercel will automatically deploy when you push to your main branch
2. Or deploy manually via Vercel dashboard or `vercel` CLI
3. Check deployment status in Vercel dashboard

---

## Step 5: Testing the Deployment
1. Open your Vercel deployment URL (e.g., `https://your-app.vercel.app`)
2. Test all frontend pages
3. Test backend API at `https://your-app.vercel.app/api/health`
4. Test file upload, reconciliation, etc.

---

## Notes on SQLite Limitations
Vercel's serverless functions are ephemeral - SQLite databases won't persist between function invocations. For production:
- Use **Vercel Postgres** (managed PostgreSQL)
- Or use **Supabase** (free tier available)
- Update `backend/config.py` to use PostgreSQL instead of SQLite

---

## Optional: CLI Deployment
1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel` (from project root)
4. Production deploy: `vercel --prod`
