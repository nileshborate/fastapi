"""expand: add name next to title - the old AND the new code both work

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16

Homework 60, step 1 of 2. A trigger keeps title and name equal while the old and the new code
run side by side.
0005 (contract) removes title - only after no old code is left.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import context, op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

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
BATCH = 10_000


def upgrade() -> None:
    op.add_column("courses", sa.Column("name", sa.Text))        # nullable: instant
    op.execute(SYNC)
    if context.is_offline_mode():                                # --sql: one statement to read
        op.execute("UPDATE courses SET name = title WHERE name IS NULL")
        return
    # the backfill in batches of 10,000 ids: every batch is its own short transaction
    with op.get_context().autocommit_block():
        conn = op.get_bind()
        last = conn.execute(sa.text("SELECT coalesce(max(id), 0) FROM courses")).scalar_one()
        for start in range(1, last + 1, BATCH):
            conn.execute(sa.text("UPDATE courses SET name = title WHERE id >= :a AND id < :b "
                                 "AND name IS NULL"), {"a": start, "b": start + BATCH})


def downgrade() -> None:
    op.execute("DROP TRIGGER courses_sync_name ON courses")
    op.execute("DROP FUNCTION courses_sync_name()")
    op.drop_column("courses", "name")
