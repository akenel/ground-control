"""TIG · Tempest — data models (GO-LIVE Phase 2).

SQLAlchemy 2.0 declarative, mirroring freehold's style. The load-bearing idea:
**identity is not a table.** Keycloak owns users; we store the Keycloak
`preferred_username` as a plain indexed string and own rows by it. A Player row is
created lazily on first login (Phase 3). Phase 2 just defines + migrates the tables.
"""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):                    # mirrors freehold Profile — lazily created on first login
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)   # Keycloak preferred_username
    display_name: Mapped[str] = mapped_column(String(120), default="")
    tagline: Mapped[str] = mapped_column(String(160), default="")
    avatar_key: Mapped[str | None] = mapped_column(String(200), nullable=True)   # MinIO object key
    banner_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Score(Base):                     # mirrors freehold Ticket — owned by string match
    __tablename__ = "scores"
    id: Mapped[int] = mapped_column(primary_key=True)
    player_username: Mapped[str] = mapped_column(String(80), index=True)
    points: Mapped[int] = mapped_column(Integer, index=True)      # indexed for ORDER BY points DESC
    level: Mapped[int] = mapped_column(Integer, default=1)
    waves: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)  # anti-cheat gate (Phase 6)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Presence(Base):                  # "who's online now" — a heartbeat row per player
    __tablename__ = "presence"
    username: Mapped[str] = mapped_column(String(80), primary_key=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
