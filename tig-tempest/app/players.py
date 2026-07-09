"""Player records — lazily created on first login (freehold's profiles pattern).

No "create on signup" step: the row springs into existence the first time a
logged-in player touches the app.
"""
from sqlalchemy import select

from db import async_session
from models import Player


async def upsert(username: str, display_name: str = "") -> None:
    async with async_session() as s:
        existing = (
            await s.execute(select(Player).where(Player.username == username))
        ).scalar_one_or_none()
        if existing:
            return
        s.add(Player(username=username, display_name=display_name or username))
        await s.commit()
