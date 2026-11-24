# The schema as SQLAlchemy sees it - ONLY for Alembic: `alembic check` compares it with the
# database. The api itself keeps using plain SQL through psycopg (app/db.py).
import sqlalchemy as sa

metadata = sa.MetaData()

courses = sa.Table(
    "courses", metadata,
    sa.Column("id", sa.Integer, sa.Identity(always=True), primary_key=True),
    sa.Column("title", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
              server_default=sa.func.now()),
    sa.Column("description", sa.Text),
    sa.Column("level", sa.Text, nullable=False, server_default="beginner"),        # 0002
    sa.CheckConstraint("length(title) BETWEEN 3 AND 80", name="courses_title_check"),
    sa.CheckConstraint("level IN ('beginner', 'intermediate', 'advanced')",
                       name="courses_level_check"),
    sa.Index("ix_courses_created_at", "created_at"),                               # 0003
)
