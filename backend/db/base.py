import json
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator, Text

from backend.config import get_settings


class JSONType(TypeDecorator):
    """SQLite-compatible JSON type that stores data as TEXT"""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str:
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)


settings = get_settings()
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    type_annotation_map = {
        dict: JSONType,
        list: JSONType,
        dict | list: JSONType,
    }
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
