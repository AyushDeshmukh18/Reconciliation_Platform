import asyncio
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from backend.api.main import create_app
from backend.db.base import Base
from backend.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield f"sqlite+aiosqlite:///{db_path}"
    os.unlink(db_path)


@pytest.fixture(scope="function")
async def async_engine(temp_db: str):
    engine = create_async_engine(
        temp_db,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session_factory(async_engine):
    return async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture(scope="function")
async def db_session(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture(scope="function")
def test_settings(temp_db):
    return Settings(
        DATABASE_URL=temp_db,
        UPLOADS_DIR=tempfile.mkdtemp(),
        APP_ENV="development",
    )


@pytest.fixture(scope="function")
def client(test_settings, session_factory):
    app = create_app()
    return TestClient(app, base_url="http://testserver")
