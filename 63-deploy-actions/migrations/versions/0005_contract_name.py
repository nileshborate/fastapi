"""contract: name NOT NULL, title gone - only when no old code is running

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-16

Homework 60, step 2 of 2 - and a safe NOT NULL on a big table (homework 60, part 2).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# a migration never imports another one: they must not change after they ran
SYNC = """
CREATE FUNCTION courses_sync_name() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.name := coalesce(NEW.name, NEW.title);      -- the old code writes title
        NEW.title := coalesce(NEW.title, NEW.name);     -- the new code writes name
    ELSIF NEW.name IS DISTINCT FROM OLD.name THEN
        NEW.title := NEW.name;
    ELSIF NEW.title IS DISTINCT FROM OLD.title THEN
        NEW.name := NEW.title;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER courses_sync_name BEFORE INSERT OR UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION courses_sync_name();
"""


def upgrade() -> None:
    op.execute("DROP TRIGGER courses_sync_name ON courses")
    op.execute("DROP FUNCTION courses_sync_name()")
    # 1. NOT VALID: checks only NEW rows - a short lock, no table scan
    op.execute("ALTER TABLE courses ADD CONSTRAINT courses_name_not_null "
               "CHECK (name IS NOT NULL) NOT VALID")
    op.execute("ALTER TABLE courses ADD CONSTRAINT courses_name_check "
               "CHECK (length(name) BETWEEN 3 AND 80) NOT VALID")
    # 2. VALIDATE in its OWN transaction: reads every row, but writes go on.
    #    (in the same transaction, the lock from step 1 would still be held)
    with op.get_context().autocommit_block():
        op.execute("ALTER TABLE courses VALIDATE CONSTRAINT courses_name_not_null")
        op.execute("ALTER TABLE courses VALIDATE CONSTRAINT courses_name_check")
    # 3. SET NOT NULL: PostgreSQL 12+ trusts the valid CHECK - no second scan
    op.alter_column("courses", "name", nullable=False)
    op.drop_constraint("courses_name_not_null", "courses", type_="check")
    op.drop_column("courses", "title")                  # drops courses_title_check too


def downgrade() -> None:
    op.add_column("courses", sa.Column("title", sa.Text))
    op.execute("UPDATE courses SET title = name")
    op.alter_column("courses", "title", nullable=False)
    op.create_check_constraint("courses_title_check", "courses",
                               "length(title) BETWEEN 3 AND 80")
    op.drop_constraint("courses_name_check", "courses", type_="check")
    op.alter_column("courses", "name", nullable=True)
    op.execute(SYNC)
