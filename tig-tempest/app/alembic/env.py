"""Alembic env — runs migrations synchronously with psycopg (app runs async).

Reads the same DATABASE_URL as the app and rewrites it to the sync psycopg driver,
so no URL/secret lives in alembic.ini. Mirrors freehold/app/alembic/env.py.
"""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from models import Base

config = context.config


def _sync_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    for prefix in ("postgresql+asyncpg://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


config.set_main_option("sqlalchemy.url", _sync_url())

if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass  # alembic.ini carries no logging config — that's fine

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=_sync_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
