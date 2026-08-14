"""Who's online now — a heartbeat table, no websockets.

The game POSTs /api/ping every ~20s; "online" = last_seen within the window.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from db import async_session
from models import Presence


async def ping(username: str) -> None:
    async with async_session() as s:
        stmt = pg_insert(Presence).values(username=username, last_seen=func.now())
        stmt = stmt.on_conflict_do_update(
            index_elements=["username"], set_={"last_seen": func.now()},
        )
        await s.execute(stmt)
        await s.commit()


async def online(within_seconds: int = 60) -> list[str]:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
    async with async_session() as s:
        return list((await s.execute(
            select(Presence.username).where(Presence.last_seen > cutoff)
            .order_by(Presence.last_seen.desc())
        )).scalars().all())
