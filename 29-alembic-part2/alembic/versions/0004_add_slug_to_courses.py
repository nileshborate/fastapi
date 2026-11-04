"""add slug to courses

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-30 13:54:24.799245

"""
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# A small, FROZEN copy of the table - never import app.models in a migration (the models change later)
courses = sa.table(
    "courses",
    sa.column("id", sa.Integer),
    sa.column("title", sa.String),
    sa.column("slug", sa.String),
)


def slugify(text: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", text.lower()))       # "FastAPI Basics!" -> "fastapi-basics"


def upgrade() -> None:
    """Upgrade schema."""
    # 1. add the column - NULL allowed for now (the old rows have no slug yet)
    with op.batch_alter_table("courses") as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=120), nullable=True))

    # 2. the DATA migration: fill every old row
    conn = op.get_bind()
    for course_id, title in conn.execute(sa.select(courses.c.id, courses.c.title)):
        conn.execute(courses.update().where(courses.c.id == course_id).values(slug=slugify(title)))

    # 3. now every row has a value: NOT NULL + UNIQUE
    with op.batch_alter_table("courses") as batch_op:
        batch_op.alter_column("slug", existing_type=sa.String(length=120), nullable=False)
        batch_op.create_unique_constraint(batch_op.f("uq_courses_slug"), ["slug"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_constraint(batch_op.f("uq_courses_slug"), type_="unique")
        batch_op.drop_column("slug")
