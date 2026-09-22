"""Async SQLAlchemy engine/session setup."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

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


_connect_args: dict = {}
if settings.db_ssl_require:
    _connect_args["ssl"] = "require"
if settings.db_disable_prepared_statement_cache:
    # Required under pgbouncer/Supavisor transaction-mode pooling — asyncpg's
    # prepared-statement cache doesn't survive statements being routed to a
    # different backend connection between calls.
    _connect_args["statement_cache_size"] = 0

_engine_kwargs: dict = {"echo": False, "connect_args": _connect_args}
if settings.db_disable_prepared_statement_cache:
    # The pooler is already doing connection pooling server-side; don't
    # also hold a local pool of long-lived connections against it.
    _engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(_normalize_database_url(settings.database_url), **_engine_kwargs)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
