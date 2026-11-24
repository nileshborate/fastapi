"""baseline - the courses table exactly as Video 59 (+ homework) left it

Revision ID: 0001
Revises:
Create Date: 2026-11-15

An EXISTING database already has this table: `alembic stamp 0001` there (mark it, run nothing).
A NEW database (tests, CI, a new server) runs it.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer, sa.Identity(always=True), primary_key=True),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("description", sa.Text),
        sa.CheckConstraint("length(title) BETWEEN 3 AND 80", name="courses_title_check"),
    )


def downgrade() -> None:
    op.drop_table("courses")
