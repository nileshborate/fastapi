"""instructors and fee paise

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-02 08:50:39.395731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008'
down_revision: Union[str, Sequence[str], None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# a small, frozen copy of the table (never import app.models in a migration)
courses = sa.table("courses", sa.column("fee", sa.Double), sa.column("fee_paise", sa.Integer))


def upgrade() -> None:
    """Upgrade schema."""
    # autogenerate wrote: create_table("instructors") + drop_table("teachers") - every teacher would be LOST
    # 1. rename the table - the rows stay
    op.rename_table("teachers", "instructors")

    with op.batch_alter_table("courses") as batch_op:
        # 2. the foreign key points to the new table name
        batch_op.drop_constraint("fk_courses_teacher_id_teachers", type_="foreignkey")
        batch_op.create_foreign_key("fk_courses_teacher_id_instructors", "instructors", ["teacher_id"], ["id"])
        # 3. a data migration: nullable first ...
        batch_op.add_column(sa.Column("fee_paise", sa.Integer(), nullable=True))

    # ... fill every old row: 299.5 -> 29950 ...
    op.execute(courses.update().values(fee_paise=sa.cast(sa.func.round(courses.c.fee * 100), sa.Integer)))

    # ... then NOT NULL
    with op.batch_alter_table("courses") as batch_op:
        batch_op.alter_column("fee_paise", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_column("fee_paise")
        batch_op.drop_constraint("fk_courses_teacher_id_instructors", type_="foreignkey")
    op.rename_table("instructors", "teachers")             # rename FIRST ...
    with op.batch_alter_table("courses") as batch_op:      # ... then point the key at "teachers" (PostgreSQL checks it)
        batch_op.create_foreign_key("fk_courses_teacher_id_teachers", "teachers", ["teacher_id"], ["id"])
