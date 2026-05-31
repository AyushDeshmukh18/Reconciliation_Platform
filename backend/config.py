from functools import lru_cache
from pathlib import Path
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE), 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database configuration - supports Vercel Postgres and SQLite
    # Vercel provides POSTGRES_URL environment variable for managed Postgres
    DATABASE_URL: str = f"sqlite+aiosqlite:///{_ROOT / 'app.db'}"
    DATABASE_SYNC_URL: str = f"sqlite:///{_ROOT / 'app.db'}"
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT_SECONDS: int = 10
    OLLAMA_CIRCUIT_BREAKER_THRESHOLD: int = 3
    OLLAMA_CIRCUIT_BREAKER_RESET_SECONDS: int = 300
    APP_NAME: str = "Reconciliation Platform"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str | None = None
    FRONTEND_URL: str = "http://localhost:5173,http://localhost:5174"
    REPORTS_DIR: str = str(_ROOT / "reports")
    UPLOADS_DIR: str = str(_ROOT / "uploads")
    RECON_RUN_CUTOFF_HOUR: int = 8
    RECON_PENDING_ESCALATION_HOURS: int = 72
    RECON_LOOKBACK_DAYS: int = 120
    RECON_DUPLICATE_WINDOW_SECONDS: int = 60
    RECON_SETTLEMENT_FILE_CUTOFF_HOUR: int = 8
    DEFAULT_CURRENCY: str = "INR"
    
    # Vercel-specific: Check for Vercel's POSTGRES_URL env var
    def model_post_init(self, __context):
        # If POSTGRES_URL is available (Vercel Postgres), use that instead of SQLite
        if os.environ.get("POSTGRES_URL"):
            # Convert postgres:// to postgresql+asyncpg:// for async SQLAlchemy
            pg_url = os.environ["POSTGRES_URL"].replace("postgres://", "postgresql+asyncpg://", 1)
            self.DATABASE_URL = pg_url
            # Convert for sync SQLAlchemy
            sync_pg_url = os.environ["POSTGRES_URL"].replace("postgres://", "postgresql://", 1)
            self.DATABASE_SYNC_URL = sync_pg_url
        
        # If VERCEL_URL is available, add it to FRONTEND_URL
        if os.environ.get("VERCEL_URL"):
            vercel_frontend = f"https://{os.environ['VERCEL_URL']}"
            if vercel_frontend not in self.FRONTEND_URL:
                self.FRONTEND_URL = f"{self.FRONTEND_URL},{vercel_frontend}"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    print(f"[Config] Using DATABASE_URL: {settings.DATABASE_URL}")
    return settings
