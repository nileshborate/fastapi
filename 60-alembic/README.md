# 60 – Alembic migrations in production

**Video 60** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Videos 28–29 taught Alembic on a laptop: `revision`, `upgrade`, `downgrade`, autogenerate, renames, data migrations.
This video is about the **real server**: a PostgreSQL that already has data, an app that runs in Compose, two copies
that start at the same time, a table that's busy, and a pipeline that must catch a broken migration **before** deploy.

Course Hub 1.8.0 – the app no longer creates tables. **Alembic owns the schema:**

```
docker compose up -d
  db       postgres:16 · volume pgdata · pg_isready -h 127.0.0.1             (healthy)
  migrate  coursehub:1.8.0 · alembic upgrade head · EXITS                     Exited (0)
  api      coursehub:1.8.0 · depends_on: migrate: service_completed_successfully
```

## Run it
```bash
cd 60-alembic
cp .env.example .env                  # Windows: copy .env.example .env
docker compose up -d --build          # db healthy -> migrate exits 0 -> api starts
docker compose ps -a                  # migrate  Exited (0)
curl localhost:8000/health/ready      # {"status":"ready","version":"1.8.0","revision":"0003"}
docker compose run --rm migrate alembic current      # 0003 (head)
docker compose run --rm migrate alembic history

pip install -r requirements-dev.txt   # the tests need the db service running
pytest --cov                          # 19 passed · coverage 98.26 %
```
**Coming from Video 59 with data in the volume?** The table already exists – run
`docker compose run --rm migrate alembic stamp 0001` once, then `docker compose up -d` (see below).

## Project
```
alembic.ini                  script_location = migrations · NO database URL in here
migrations/env.py            DATABASE_URL from our settings · one migrator at a time · lock_timeout
migrations/versions/
  0001_baseline.py           the courses table EXACTLY as Video 59 (+ homework) left it
  0002_add_level.py          level text NOT NULL DEFAULT 'beginner' + a CHECK
  0003_index_created_at.py   CREATE INDEX CONCURRENTLY - in an autocommit_block
app/tables.py                the schema as SQLAlchemy Core - only for `alembic check`
app/db.py                    the pool (no CREATE TABLE any more) · revision() reads alembic_version
app/main.py                  /health/ready: 503 "migrations pending" if the database isn't at head
compose.yaml                 db + migrate (one-shot) + api · x-app: a YAML anchor for the shared parts
Dockerfile                   ONE image for api AND migrate: + alembic.ini + migrations/
tests/test_migrations.py     8 tests: one head · down+up · no drift · stamp · 2 migrators · lock_timeout · --sql
tests/test_app.py            8 tests · test_healthcheck.py (3) · conftest.py: migrates the TEST database
```

## The production rules
| | |
|---|---|
| **The app never creates tables** | `CREATE TABLE IF NOT EXISTS` at startup can't rename, can't add a column (homework 59), can't go back |
| **A one-shot `migrate` service** | same image, `command: alembic upgrade head`, `restart: "no"`; the api waits for `service_completed_successfully` |
| **Not in the api's startup** | 3 replicas = 3 migrators at once. A separate step runs once, before the new code |
| **An existing database: `stamp`** | `alembic stamp 0001` writes the version and runs nothing – the baseline matches what's there |
| **One migrator at a time** | `pg_try_advisory_lock` in `env.py` – a 2nd copy waits, then finds nothing to do |
| **`lock_timeout`** | an `ALTER TABLE` waiting for its lock makes **every** query on that table wait behind it – give up after 5 s, retry |
| **Transactional DDL** | PostgreSQL rolls back a failed migration completely – even `CREATE TABLE` (MySQL can't) |
| **Constant defaults are free** | PostgreSQL 11+: `ADD COLUMN … NOT NULL DEFAULT 'beginner'` stores the default once – no rewrite |
| **`CREATE INDEX CONCURRENTLY`** | writes go on while the index is built; it can't run in a transaction → `autocommit_block()` |
| **The app checks the revision** | new code on an old schema → `/health/ready` 503 – the load balancer sends no traffic |
| **Roll forward** | downgrades are tested in CI, but in production you fix with a **new** migration (data may be gone) |
| **Review the SQL** | `alembic upgrade 0001:head --sql` prints the SQL – nothing runs |

## What the runs showed – real numbers
My machine can't reach Docker Hub, so `db` ran a **local stand-in** image: Ubuntu 24.04 + PostgreSQL 16.15 with
the same environment variables, data directory and init rules as the official image (`PG_IMAGE` in my `.env`).
The 1.8.0 image: `docker build` 18.12 s, 276 MB (Alembic + SQLAlchemy add 26 MB).

| | |
|---|---|
| 1.8.0 on the Video 59 volume (3 courses) | migrate: `Running upgrade  -> 0001` → `DuplicateTable: relation "courses" already exists` → `Exited (1)`; `up -d` said `service "migrate" didn't complete successfully: exit 1`; api: `Created`, never started; `\dt` – only `courses`, **no** `alembic_version` (rolled back) |
| `docker compose run --rm migrate alembic stamp 0001` | `Running stamp_revision  -> 0001` (2.57 s) |
| `docker compose up -d` | migrate: `0001 -> 0002`, `0002 -> 0003` → `Exited (0)` → api started (3.00 s). The 3 old courses: `"level":"beginner"` |
| `up -d` again | migrate starts, takes the lock, runs nothing, exits 0 (3.38 s) |
| `alembic downgrade 0002` (code still at 0003) | `/health/ready` → `{"status":"not_ready","database":"migrations pending","revision":"0002","expected":"0003"}` **503**; `run --rm migrate` → 200 |
| app 1.8.0 on a database at 0001 | `POST /courses` → **500** `UndefinedColumn: column "level" of relation "courses" does not exist` |
| 1,000,000 rows: `INSERT … generate_series` | 3.04 s |
| `alembic upgrade 0002` / `0003` on 1M rows | 1.859 s / 1.858 s – minus 1.618 s for Python + connecting (`alembic current`) ≈ **0.24 s each** |
| the old way: add the column, `UPDATE` every row, `SET NOT NULL` | `UPDATE 1000009` **6,228 ms** + 125 ms – and every row locked (rolled back) |
| a 20 s transaction reads `courses`, migrate **without** `lock_timeout` | `pg_stat_activity`: `ALTER TABLE` – Lock, `INSERT` – **Lock**. A plain `INSERT` from another client waited **14.70 s**; the migration took 19.40 s |
| the same with `lock_timeout = 5s` | `canceling statement due to lock timeout` (7.69 s, exit 1), still at `0001`; the `INSERT` waited 3.96 s; after that 0.16 s. Retry after the long transaction: ok |
| two migrators at the same time | B: `another migrator is running - waiting` → `got the migration lock` → nothing to do. A ran 0002 + 0003. Both exit 0 |
| `alembic upgrade 0001:head --sql` | `BEGIN; … ADD COLUMN level … ; COMMIT; CREATE INDEX CONCURRENTLY …; BEGIN; UPDATE alembic_version …` |

**My first lock deadlocked.** `env.py` first used a blocking `SELECT pg_advisory_lock(…)`. Two migrators at once:
`DeadlockDetected – Process 329 waits for ExclusiveLock on advisory lock [16385,0,60000,1]; blocked by process 328.
Process 328 waits for ShareLock on virtual transaction 4/62; blocked by process 329.` The waiting migrator sat in an open
transaction – and `CREATE INDEX CONCURRENTLY` (0003) waits for **every** open transaction to finish. The fix:
`pg_try_advisory_lock` in a loop with `rollback()` + `sleep(1)` – nothing open while it waits.

**`alembic check` catches drift.** I added `price` to `app/tables.py` without a migration:
`FAILED: New upgrade operations detected: [('add_column', None, 'courses', Column('price', Integer(), …))]` – exit code
255, so the CI step fails. `alembic revision --autogenerate -m "add price"` then wrote the migration.

**CI (`.github/workflows/ci-60.yml`), run the way a runner does:** lint ✓ · test 3.12: 19 passed (pytest 10.08 s) ·
test 3.13: 19 passed (8.76 s) · migrations: one head 0.45 s · up from nothing 0.61 s · `alembic check` 0.77 s
(`No new upgrade operations detected.`) · down to base + up 1.34 s · `--sql` → `migration.sql` (543 bytes) uploaded.
The service container was `(healthy)` after 2.3 s. `actionlint` + the JSON schema check: no problems.

## Interview questions
1. **Where do you run migrations in production – and why not in the app's startup?** As a separate step **before** the
   new code: a one-shot job (Compose `migrate`, a Kubernetes Job, a pipeline step). In the startup, every replica would
   migrate at the same time, a slow migration would block the start, and a failure would crash-loop the app.
2. **You add Alembic to a project whose database already exists. What do you do?** Write a baseline migration that
   matches the existing schema exactly, then `alembic stamp <baseline>` on that database – it records the version
   without running anything. New databases run the baseline normally.
3. **Why can a small `ALTER TABLE` take the whole site down?** It needs an `ACCESS EXCLUSIVE` lock. If a long transaction
   holds a lock on the table, the `ALTER` waits – and every new query on that table queues **behind** it. Set
   `lock_timeout`, let the migration fail fast, and retry.

## Homework
1. **Expand and contract:** rename `title` → `name` with **zero downtime**: 0004 adds `name` and copies the data
   (old and new code both work), then 0005 drops `title` – after the new code is everywhere. Why not `rename_column`?
2. **A safe NOT NULL on a big table:** add `CHECK (description IS NOT NULL) NOT VALID`, then
   `VALIDATE CONSTRAINT` in a second step – and measure the lock each step takes on 1,000,000 rows.
3. **Migrations in the Docker job of CI:** in `ci-60.yml`, start `db` + `migrate` + `api` with Compose and smoke-test
   `/health/ready` – it must say `"revision": "0003"`.

Answer at the start of Video 61 (Nginx + HTTPS in front of the api).
