"""Scores + leaderboard queries — freehold's tickets.py patterns (service owns all SQL).

Session-per-operation; leaderboard = each player's personal best, ranked.
"""
from sqlalchemy import func, select

from db import async_session
from models import Score


async def submit(username, points, level=1, waves=0, duration_ms=0, verified=False) -> int:
    async with async_session() as s:
        row = Score(
            player_username=username, points=points, level=level,
            waves=waves, duration_ms=duration_ms, verified=verified,
        )
        s.add(row)
        await s.commit()
        return row.id


async def personal_best(username) -> int:
    async with async_session() as s:
        v = (await s.execute(
            select(func.max(Score.points)).where(Score.player_username == username)
        )).scalar()
        return int(v or 0)


async def last_score(username):
    async with async_session() as s:
        return (await s.execute(
            select(Score).where(Score.player_username == username)
            .order_by(Score.created_at.desc()).limit(1)
        )).scalar_one_or_none()


async def recent(username, limit=5):
    async with async_session() as s:
        return list((await s.execute(
            select(Score).where(Score.player_username == username)
            .order_by(Score.created_at.desc()).limit(limit)
        )).scalars().all())


async def leaderboard(limit=20):
    """Per-player personal best, ranked. Returns [(username, best, top_level)]."""
    async with async_session() as s:
        rows = (await s.execute(
            select(
                Score.player_username,
                func.max(Score.points).label("best"),
                func.max(Score.level).label("lvl"),
            )
            .group_by(Score.player_username)
            .order_by(func.max(Score.points).desc())
            .limit(limit)
        )).all()
        return [(r[0], int(r[1]), int(r[2])) for r in rows]


async def rank(username) -> int | None:
    """1-based rank by personal best across all players (None if no scores yet)."""
    best = await personal_best(username)
    if best <= 0:
        return None
    async with async_session() as s:
        bests = select(
            Score.player_username, func.max(Score.points).label("best"),
        ).group_by(Score.player_username).subquery()
        higher = (await s.execute(
            select(func.count()).select_from(bests).where(bests.c.best > best)
        )).scalar()
        return int(higher or 0) + 1
