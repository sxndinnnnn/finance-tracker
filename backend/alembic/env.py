"""Alembic migration environment — wires Alembic to the app's settings and
metadata so `alembic revision --autogenerate` picks up every model."""
import asyncio
from logging.config import fileConfig

from alembic import context

from app.core.config import get_settings
# Reuse the app's own engine rather than building a second one from the raw
# DATABASE_URL: that's what applies the postgres:// -> postgresql+asyncpg://
# rewrite and the managed-Postgres SSL connect_args (see database.py) —
# duplicating that logic here would silently drift out of sync with it.
from app.core.database import Base, engine
import app.models  # noqa: F401 — ensures every model is registered on Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
