"""index courses.created_at - built CONCURRENTLY

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-15
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # CONCURRENTLY: writes go on while the index is built - but it can't run in a transaction,
    # so Alembic commits first (autocommit_block)
    with op.get_context().autocommit_block():
        op.create_index("ix_courses_created_at", "courses", ["created_at"],
                        postgresql_concurrently=True)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.drop_index("ix_courses_created_at", table_name="courses",
                      postgresql_concurrently=True)
