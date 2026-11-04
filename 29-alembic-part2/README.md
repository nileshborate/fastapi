# 29 – Alembic Part 2: Autogenerate, Renames, Data Migrations, Batch Mode & Teamwork

**FastAPI Mastery: Zero to Production** – Video 29 · Nilesh Technology

In Part 1 we wrote every migration by hand. Now **autogenerate** writes them for us – by comparing our models
with the database. But it's a *draft*: today we learn what it gets right, what it gets WRONG (renames!),
and how real teams use it.

## The project (fresh and small)
```
29-alembic-part2/
├── alembic.ini
├── alembic/
│   ├── env.py                  # target_metadata + render_as_batch=True (SQLite)
│   └── versions/
│       ├── 0001_create_courses_table.py        # autogenerate
│       ├── 0002_add_teachers.py                # autogenerate + batch mode (a foreign key on SQLite)
│       ├── 0003_rename_price_to_fee.py         # autogenerate got it WRONG - fixed by hand
│       ├── 0004_add_slug_to_courses.py         # a DATA migration (3 steps)
│       ├── 0005_add_level_to_courses.py        # Asha's branch  ┐ two heads!
│       ├── 0006_add_description_to_courses.py  # Ravi's branch  ┘
│       └── 0007_merge_asha_and_ravi.py         # alembic merge heads
├── app/                        # database.py (naming convention) · models · schemas · routers · utils.py
└── tests/                      # test_courses.py · test_migrations.py   (10 tests)
```

## Run it
```bash
cd 29-alembic-part2
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
alembic upgrade head
fastapi dev app/main.py
pytest -v                       # 10 passed (on PostgreSQL too)
```

## The commands
| Command | What it does |
|---|---|
| `alembic revision --autogenerate -m "add teachers" --rev-id 0002` | compares `Base.metadata` with the database and WRITES the migration – always read it! |
| `alembic check` | "No new upgrade operations detected." – or fails if a model changed without a migration (great for CI) |
| `alembic heads` | the newest migration(s) – more than one = two branches |
| `alembic merge heads -m "merge"` | an (empty) migration with TWO parents – joins the branches |
| `alembic history` | shows `(branchpoint)` and `(mergepoint)` |

## 1. A naming convention (database.py)
```python
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
```
Every constraint gets a predictable name (`uq_courses_title`, `fk_courses_teacher_id_teachers`) – you need the name to drop or change it later.

## 2. Batch mode – SQLite can't ALTER constraints (env.py)
Without it: `NotImplementedError: No support for ALTER of constraints in SQLite dialect.`
```python
context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
```
`with op.batch_alter_table("courses") as batch_op:` → on SQLite: CREATE `_alembic_tmp_courses` → INSERT … SELECT → DROP → RENAME.
On PostgreSQL: a normal `ALTER TABLE`.

## 3. Autogenerate can't see a rename
It wrote `add_column("fee")` + `drop_column("price")` – every price would be LOST
(here: `IntegrityError: NOT NULL constraint failed: _alembic_tmp_courses.fee`). Fix it by hand:
```python
with op.batch_alter_table("courses") as batch_op:
    batch_op.alter_column("price", new_column_name="fee")      # PostgreSQL: ALTER TABLE courses RENAME price TO fee
```

## 4. A data migration – a NOT NULL, UNIQUE slug for old rows
```python
courses = sa.table("courses", sa.column("id", sa.Integer), sa.column("title", sa.String), sa.column("slug", sa.String))
# 1. add the column, NULL allowed   2. fill every old row   3. NOT NULL + UNIQUE
conn = op.get_bind()
for course_id, title in conn.execute(sa.select(courses.c.id, courses.c.title)):
    conn.execute(courses.update().where(courses.c.id == course_id).values(slug=slugify(title)))
```
Never import `app.models` in a migration – the models change, the migration must not.
(A data migration that reads rows needs a live database – it can't run with `--sql`.)

## 5. Teamwork: two heads
Asha and Ravi both create a migration on top of 0004 → `alembic upgrade head`:
`Multiple head revisions are present for given argument 'head'` → `alembic merge heads -m "merge asha and ravi"`
→ `down_revision = ('0005', '0006')`. A test keeps it from happening again:
```python
assert ScriptDirectory.from_config(alembic_cfg).get_heads() == ["0007"]
```

## Interview questions
1. **What can't Alembic autogenerate detect?** Renames of tables and columns (it sees a drop + an add), and – by default – changes of server defaults. Some constraint and type changes depend on the database. That's why you ALWAYS read the generated file.
2. **What is a data migration, and how do you add a NOT NULL column to a table with rows?** A migration that changes the DATA, not only the schema. Add the column as nullable, fill the old rows (`op.get_bind()` + a small `sa.table`), then make it NOT NULL.
3. **Two developers created migrations at the same time. What happens and how do you fix it?** There are two heads, and `upgrade head` fails. `alembic merge heads` creates a migration with both as parents. A test (or `alembic heads` in CI) catches it early.

## Homework
1. Rename the table `teachers` → `instructors` (autogenerate – then fix it by hand with `op.rename_table`). Don't forget the foreign key in courses and the model.
2. A data migration: a new `fee_paise` Integer column (NOT NULL) = `fee * 100` for the old rows.
3. Tests: old rows keep their teacher after the rename; `fee_paise` is filled; still only one head.

Answer at the start of Video 30 (Association Object).
