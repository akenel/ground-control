"""init: players, scores, presence

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(80), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_players_username", "players", ["username"], unique=True)

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("player_username", sa.String(80), nullable=False),
        sa.Column("points", sa.Integer, nullable=False),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("waves", sa.Integer, nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scores_player_username", "scores", ["player_username"])
    op.create_index("ix_scores_points", "scores", ["points"])

    op.create_table(
        "presence",
        sa.Column("username", sa.String(80), primary_key=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("presence")
    op.drop_index("ix_scores_points", table_name="scores")
    op.drop_index("ix_scores_player_username", table_name="scores")
    op.drop_table("scores")
    op.drop_index("ix_players_username", table_name="players")
    op.drop_table("players")
