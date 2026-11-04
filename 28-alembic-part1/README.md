# 28 – Alembic Part 1: Why Migrations + the First Migration

**FastAPI Mastery: Zero to Production** – Video 28 · Nilesh Technology

Until now, every new column meant: **delete the database**. In production, with real data, that's impossible.
**Alembic** keeps a history of database changes – like git commits for your tables – and applies them in order.

## The project (fresh and small)
```
28-alembic-part1/
├── alembic.ini                 # Alembic's settings (the URL comes from .env - see env.py)
├── alembic/
│   ├── env.py                  # connects Alembic to OUR settings + Base.metadata
│   ├── script.py.mako          # the template for new migration files
│   └── versions/
│       ├── 0001_create_courses_table.py
│       └── 0002_add_level_to_courses.py
├── app/                        # models/course.py · schemas · routers · database.py · main.py (NO create_all)
└── tests/                      # test_courses.py · test_migrations.py   (8 tests)
```

## Run it
```bash
cd 28-alembic-part1
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
alembic upgrade head            # create / update the tables
fastapi dev app/main.py
pytest -v                       # 8 passed (on PostgreSQL too)
```

## The commands
| Command | What it does |
|---|---|
| `alembic init alembic` | creates `alembic.ini` + the `alembic/` folder (once per project) |
| `alembic revision -m "create courses table" --rev-id 0001` | a new, EMPTY migration file – you write `upgrade()` + `downgrade()` |
| `alembic upgrade head` | runs every migration that's not applied yet |
| `alembic downgrade -1` | undoes the last migration |
| `alembic current` | the version of THIS database (`0002 (head)`) |
| `alembic history` | all migrations, newest first |
| `alembic upgrade head --sql` | prints the SQL instead of running it |

## A migration
```python
revision = "0002"
down_revision = "0001"          # the chain: base -> 0001 -> 0002

def upgrade() -> None:
    op.add_column("courses",
        sa.Column("level", sa.String(20), nullable=False, server_default="beginner"))   # old rows get "beginner"

def downgrade() -> None:
    op.drop_column("courses", "level")
```
`ALTER TABLE courses ADD COLUMN level VARCHAR(20) DEFAULT 'beginner' NOT NULL` – and the `alembic_version` table now says `0002`.

## Interview questions
1. **What is a database migration, and why not just use `create_all()`?** A migration is a versioned, ordered change to the database schema, with an upgrade and a downgrade. `create_all()` only creates missing tables – it never changes existing ones – so it can't add a column to a table that already holds data.
2. **How does Alembic know which migrations to run?** Each migration has a `revision` and a `down_revision`, forming a chain. The database stores its current revision in the `alembic_version` table; `upgrade head` runs every migration after it, in order.
3. **How do you add a NOT NULL column to a table that already has rows?** Give it a `server_default` (or add it as nullable, fill the rows, then make it NOT NULL). Otherwise the database refuses: the existing rows would have no value.

## Homework
1. Migration **0003** (written by hand): `is_published` – Boolean, NOT NULL, `server_default=sa.false()`. Update the model and the schemas.
2. Migration **0004**: create a `teachers` table (id, name).
3. Tests: the version is `0004`; `downgrade -2` goes back to `0002` and both changes are gone.

Answer at the start of Video 29 (Alembic Part 2: autogenerate).
