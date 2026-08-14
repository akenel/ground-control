"""Player profile reads/writes (freehold's profiles.py pattern)."""
from sqlalchemy import select

from db import async_session
from models import Player


async def get(username: str) -> Player | None:
    async with async_session() as s:
        return (await s.execute(select(Player).where(Player.username == username))).scalar_one_or_none()


async def avatars_for(usernames: list[str]) -> dict[str, str | None]:
    """username -> avatar_key, for the leaderboard/board."""
    if not usernames:
        return {}
    async with async_session() as s:
        rows = (await s.execute(
            select(Player.username, Player.avatar_key).where(Player.username.in_(usernames))
        )).all()
        return {u: k for u, k in rows}


async def cards_for(usernames: list[str]) -> dict[str, tuple[str, str | None]]:
    """username -> (display_name, avatar_key), for the leaderboard rows."""
    if not usernames:
        return {}
    async with async_session() as s:
        rows = (await s.execute(
            select(Player.username, Player.display_name, Player.avatar_key)
            .where(Player.username.in_(usernames))
        )).all()
        return {u: (dn, ak) for u, dn, ak in rows}


async def update_text(username: str, display_name: str | None = None, tagline: str | None = None) -> None:
    async with async_session() as s:
        p = (await s.execute(select(Player).where(Player.username == username))).scalar_one_or_none()
        if not p:
            return
        if display_name is not None:
            p.display_name = display_name[:120]
        if tagline is not None:
            p.tagline = tagline[:160]
        await s.commit()


async def set_image(username: str, field: str, key: str) -> None:
    """field is 'avatar_key' or 'banner_key'."""
    async with async_session() as s:
        p = (await s.execute(select(Player).where(Player.username == username))).scalar_one_or_none()
        if p:
            setattr(p, field, key)
            await s.commit()
