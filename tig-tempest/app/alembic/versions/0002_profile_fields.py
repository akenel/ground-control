"""profile fields: tagline, avatar_key, banner_key

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("tagline", sa.String(160), nullable=False, server_default=""))
    op.add_column("players", sa.Column("avatar_key", sa.String(200), nullable=True))
    op.add_column("players", sa.Column("banner_key", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("players", "banner_key")
    op.drop_column("players", "avatar_key")
    op.drop_column("players", "tagline")
