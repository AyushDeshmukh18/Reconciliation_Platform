import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.exc import SQLAlchemyError

from backend.config import get_settings

def configure_logging(settings):
    level_name = settings.LOG_LEVEL.upper()
    level = getattr(logging, level_name, logging.INFO)
    handlers = [logging.StreamHandler(sys.stdout)]
    if settings.LOG_FILE:
        handlers.append(logging.FileHandler(settings.LOG_FILE, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True,
    )
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy").setLevel(logging.INFO if level > logging.INFO else level)

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger(__name__)

from backend.api.middleware import CorrelationIDMiddleware
from backend.api.routers import audit, exceptions, reconciliation, reports, transactions
from backend.api.schemas.reconciliation import JobProgressResponse
from backend.db.base import AsyncSessionLocal
from backend.jobs.celery_app import celery_app
from backend.jobs.local_tasks import get_local_job


def _error_payload(request: Request, error_code: str, message: str) -> dict:
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    return {
        "error_code": error_code,
        "message": message,
        "correlation_id": correlation_id,
        "docs_url": "/api/docs",
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("🚀 Backend starting up with config:")
    logger.info(f"  - APP_ENV: {settings.APP_ENV}")
    logger.info(f"  - LOG_LEVEL: {settings.LOG_LEVEL}")
    logger.info(f"  - DATABASE_URL: (masked)")
    logger.info(f"  - FRONTEND_URL: {settings.FRONTEND_URL}")
    
    Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

    # Create all tables
    from backend.db.base import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Run seed script (idempotent)
    logger.info("Checking seed data...")
    try:
        from backend.db.seed import load_realistic_data
        load_realistic_data()
        logger.info("Seed data check complete!")
    except Exception as e:
        logger.error(f"Error seeding database: {e}", exc_info=True)
        print(f"⚠️  Seed failed but app will continue: {e}")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Add request logging middleware FIRST
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            logger.info(f"Response status: {response.status_code} for {request.method} {request.url.path}")
            return response
        except Exception as e:
            logger.error(f"Error processing request {request.method} {request.url.path}: {e}", exc_info=True)
            raise

    # Parse FRONTEND_URL (comma-separated for multiple origins)
    origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]
    # Add default localhost origins for development
    default_origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]
    for origin in default_origins:
        if origin not in origins:
            origins.append(origin)
    # Add wildcard vercel.app origin
    if "https://*.vercel.app" not in origins:
        origins.append("https://*.vercel.app")
    logger.info("Allowing CORS origins: %s", origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIDMiddleware)

    prefix = "/api/v1"
    app.include_router(reconciliation.router, prefix=prefix)
    app.include_router(transactions.router, prefix=prefix)
    app.include_router(exceptions.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
    app.include_router(audit.router, prefix=prefix)

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(request: Request, exc: SQLAlchemyError):
        return JSONResponse(status_code=500, content=_error_payload(request, "DATABASE_ERROR", str(exc)))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content=_error_payload(request, "VALIDATION_ERROR", str(exc.errors())))

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(request, "HTTP_ERROR", detail),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content=_error_payload(request, "INTERNAL_ERROR", str(exc)))

    @app.get(f"{prefix}/jobs/{{task_id}}/progress")
    async def job_progress(task_id: str):
        async def event_stream():
            while True:
                local = get_local_job(task_id)
                if local:
                    payload = JobProgressResponse(
                        task_id=task_id,
                        status=str(local.get("status", "PENDING")),
                        progress_percent=float(local.get("progress_percent", 0)),
                        message=str(local.get("message", "Processing")),
                        eta_seconds=local.get("eta_seconds"),
                    )
                    yield f"data: {payload.model_dump_json()}\n\n"
                    if payload.status in ("SUCCESS", "FAILURE"):
                        break
                    await asyncio.sleep(1)
                    continue

                if celery_app is None:
                    payload = JobProgressResponse(
                        task_id=task_id,
                        status="SUCCESS",
                        progress_percent=100.0,
                        message="Celery not configured — task assumed complete",
                        eta_seconds=0,
                    )
                    yield f"data: {payload.model_dump_json()}\n\n"
                    break

                result = celery_app.AsyncResult(task_id)
                state = result.state
                meta = result.info if isinstance(result.info, dict) else {}
                progress = float(meta.get("progress_percent", 0 if state == "PENDING" else 100))
                message = meta.get("message", state)
                eta = meta.get("eta_seconds")

                if state == "SUCCESS" and isinstance(result.result, dict):
                    accepted = result.result.get("accepted", 0)
                    rejected = result.result.get("rejected", 0)
                    message = f"Ingestion complete — {accepted} accepted, {rejected} rejected"
                    progress = 100.0
                elif state == "FAILURE":
                    message = str(result.result) if result.result else "Task failed"
                    progress = 100.0

                payload = JobProgressResponse(
                    task_id=task_id,
                    status=state,
                    progress_percent=progress,
                    message=str(message),
                    eta_seconds=eta,
                )
                yield f"data: {payload.model_dump_json()}\n\n"

                if state in ("SUCCESS", "FAILURE"):
                    break
                await asyncio.sleep(2)

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return {
            "status": "ok", 
            "service": "reconciliation-platform", 
            "version": "1.0.0"
        }

    return app
