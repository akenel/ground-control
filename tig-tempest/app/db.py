"""Async DB engine + session, mirroring freehold/app/db.py.

One DATABASE_URL feeds runtime (asyncpg) and Alembic (psycopg, swapped in env.py).
Session-per-operation: each service function opens `async with async_session()`.
"""
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def _async_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


engine = create_async_engine(_async_url(), echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def db_check() -> tuple[bool, str]:
    """DB liveness for /healthz — a cheap round-trip."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, str(e)
