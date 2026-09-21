"""Async SQLAlchemy engine/session setup."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


def _normalize_database_url(url: str) -> str:
    """Accepts the plain postgres:// / postgresql:// URL a managed Postgres
    provider (Supabase, RDS, ...) hands you and rewrites it to the
    postgresql+asyncpg:// form SQLAlchemy's async engine needs, so pasting
    their connection string in as-is just works."""
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


_connect_args = {"ssl": "require"} if settings.db_ssl_require else {}

engine = create_async_engine(
    _normalize_database_url(settings.database_url), echo=False, connect_args=_connect_args
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
