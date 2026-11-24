"""add level to courses

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-15
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NOT NULL + a CONSTANT default: PostgreSQL 11+ only stores the default - no table rewrite
    op.add_column("courses", sa.Column("level", sa.Text, nullable=False,
                                       server_default="beginner"))
    op.create_check_constraint("courses_level_check", "courses",
                               "level IN ('beginner', 'intermediate', 'advanced')")


def downgrade() -> None:
    op.drop_constraint("courses_level_check", "courses", type_="check")
    op.drop_column("courses", "level")
