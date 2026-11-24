# 59 – PostgreSQL in Compose: a real database next to the app

**Video 59** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

Course Hub 1.7.0 moves from a SQLite file to **PostgreSQL** – as its own service in Docker Compose:

```
docker compose up -d
  db   (postgres:16)  ── volume pgdata ── healthcheck: pg_isready -h 127.0.0.1
   ▲  depends_on: condition: service_healthy
  api  (coursehub:1.7.0)  DATABASE_URL=postgresql://coursehub:…@db:5432/coursehub
```

## Run it
```bash
cd 59-postgres
cp .env.example .env                  # Windows: copy .env.example .env
docker compose up -d --build          # db: healthy -> api: started
curl localhost:8000/health/ready      # {"status":"ready","version":"1.7.0"}
docker compose exec db psql -U coursehub -c "SELECT * FROM courses"

pip install -r requirements-dev.txt   # the tests need the db service running
pytest --cov                          # 15 passed (12 + 3 homework) · coverage 98.98 %
docker compose down                   # the data stays in the volume
```

## Project
```
app/config.py     DATABASE_URL has NO default - without it the app refuses to start
app/db.py         Database: a psycopg connection pool · CREATE TABLE IF NOT EXISTS · %s parameters
                  + ALTER TABLE … ADD COLUMN IF NOT EXISTS description (homework 59)
app/main.py       lifespan opens the pool (waits up to 10 s) · /health/ready asks the database
db/init/01-test-database.sql   runs ONCE, on an empty volume: CREATE DATABASE coursehub_test
compose.yaml      db + api · .env · named volume · pg_isready · depends_on: service_healthy
tests/            test_app.py (9, against the real coursehub_test) · test_healthcheck.py (3)
                  test_homework59.py (3) · conftest.py (DATABASE_URL + the client fixture)
```

## The pieces
| | |
|---|---|
| `image: postgres:16` | pin the major version – a new major needs a dump/restore or `pg_upgrade` |
| `POSTGRES_USER / PASSWORD / DB` | from `.env` (never committed); the image creates the user and the database |
| `pgdata:/var/lib/postgresql/data` | a **named volume** – `docker compose down` keeps it, `down -v` deletes it |
| `./db/init:/docker-entrypoint-initdb.d` | `.sql` files that run **only when the volume is empty** |
| `127.0.0.1:5432:5432` | psql and pytest on your laptop – not the whole network. In production: no `ports:` at all |
| `pg_isready -h 127.0.0.1` | "accepting connections" – over TCP, the way the api connects (see below) |
| `depends_on: condition: service_healthy` | the api starts after the database is ready – not only started |
| `@db:5432` | inside Compose the **service name** is the host name; `localhost` is the api container itself |

## What the runs showed – real numbers
My machine can't reach Docker Hub, so `db` ran a **local stand-in** image: Ubuntu 24.04 + PostgreSQL 16.15
with the same environment variables, data directory and init rules as the official image (`PG_IMAGE` in my `.env`).

| | |
|---|---|
| first `docker compose up -d` (empty volume) | 3.07 s – `running /docker-entrypoint-initdb.d/01-test-database.sql` → `PostgreSQL init process complete` → db `(healthy)` → api started |
| `docker compose down` + `up -d` | 2.96 s – `PostgreSQL Database directory appears to contain a database; Skipping initialization` – both courses still there |
| `docker compose down -v` + `up -d` | `curl /courses` → `[]` – the data is gone |
| `docker compose stop db` | `/health/ready` → `{"status":"not_ready","database":"unreachable"}` **503**; `start db` → 200 again, same pool |
| `docker run --rm coursehub:1.7.0` (no DATABASE_URL) | `database_url  Field required` – the app does not start |
| `DATABASE_URL=…@localhost:5432/…` in the api | `connection to server at "127.0.0.1", port 5432 failed: Connection refused` → `Application startup failed. Exiting.` |
| `pytest --cov` (Python 3.12 / 3.13) | 12 passed – 3.83 s / 3.21 s – coverage 98.97 % |

**The password trap.** `POSTGRES_PASSWORD` is used **once** – when the volume is empty. I changed it in `.env`,
`docker compose up -d` recreated both containers, and the api got the new password … the database still had the old one:
`FATAL: password authentication failed for user "coursehub"` → `Application startup failed` → restart, again and again.
Fix without losing data: `docker compose exec db psql -U coursehub -c "ALTER USER coursehub PASSWORD '…'"` – 14 s later
the api was `(healthy)` with both courses.

**`pg_isready` without `-h`: healthy too early.** While the init scripts run, the entrypoint starts a temporary server that
listens **only on the Unix socket**. `pg_isready` (socket) said *accepting* – the api connected over TCP and got
`Connection refused` 3 times (an init script with `pg_sleep(6)`; `up -d` returned after 2.01 s). With `-h 127.0.0.1`:
`up -d` waited 8.57 s and the api saw 0 errors. Our pool also waits up to 10 s (`DB_WAIT_S`) – two safety nets.

## Interview questions
1. **How does the api container find the database in Compose?** Compose puts both services on one network with DNS:
   the service name `db` is the host name. `localhost` inside the api container is the api container itself.
2. **What is the difference between `depends_on` and `condition: service_healthy`?** The short form only waits until
   the db container is **started**; the condition waits for its health check – PostgreSQL accepting connections.
3. **You changed `POSTGRES_PASSWORD` and the app can't log in. Why?** The variables only initialise an **empty** data
   directory. With an existing volume they are ignored – change the password with `ALTER USER`, or (dev only) `down -v`.

## Homework
1. **CI with a real PostgreSQL:** a workflow `ci-59.yml` with a `services: postgres` container and a health check –
   `pytest` against it on every push.
2. **Backup and restore:** `pg_dump` from the db container into `backup.sql`, `down -v`, `up -d`, restore with `psql` –
   and show that the courses are back.
3. **A new column:** add `description text` to `courses` – and see why `CREATE TABLE IF NOT EXISTS` does **not** add it
   to an existing table. Do it with `ALTER TABLE … ADD COLUMN IF NOT EXISTS` without losing the data.

Answer at the start of Video 60 (Alembic migrations in production).

## Homework answer (shown at the start of Video 60)

### 1. CI with a real PostgreSQL – `.github/workflows/ci-59.yml`
```yaml
  test:
    services:
      postgres:                             # GitHub starts it BEFORE the first step ...
        image: postgres:16
        env:
          POSTGRES_USER: coursehub
          POSTGRES_PASSWORD: coursehub-dev  # a throwaway CI database - not a real secret
          POSTGRES_DB: coursehub_test       # the tests' database: no init script needed
        ports:
          - 5432:5432                       # the job runs on the runner -> localhost:5432
        options: >-
          --health-cmd "pg_isready -h 127.0.0.1 -U coursehub -d coursehub_test"
          --health-interval 2s
          --health-timeout 3s
          --health-retries 15
    steps:
      ...
      - run: pytest --cov
        env:
          TEST_DATABASE_URL: postgresql://coursehub:coursehub-dev@localhost:5432/coursehub_test
```
The job runs **on the runner**, so the service is `localhost:5432` (a job inside a `container:` would use `postgres:5432`).
I ran the workflow the way a runner does (the service container first, then a fresh copy and a fresh virtual environment):
the service was `(healthy)` after **2.37 s**, `pip install` 12.91 s, `pytest --cov` 4.17 s – **15 passed**, coverage 98.98 %.
`actionlint` and the JSON schema check: no problems.

### 2. Backup and restore with `pg_dump`
```bash
docker compose exec -T db pg_dump -U coursehub --clean --if-exists coursehub > backup.sql
docker compose down -v && docker compose up -d                  # an empty database
docker compose exec -T db psql -U coursehub -d coursehub -v ON_ERROR_STOP=1 -q < backup.sql
```
`-T` = no terminal – needed when you redirect with `>` or `<`. What my runs showed:
| | |
|---|---|
| plain `pg_dump`, restore with `ON_ERROR_STOP=1` | `ERROR: relation "courses" already exists` – **our app started first and created the empty table**; nothing restored |
| the same file without `ON_ERROR_STOP` | 3 errors (`courses`, `courses_id_seq`, `multiple primary keys`) … and `COPY 3` – the rows came back, but by luck |
| `pg_dump --clean --if-exists` | the dump starts with `DROP TABLE IF EXISTS public.courses;` – restore: no errors, all 4 courses back, `setval … 4`, the next POST got **id 5** |

### 3. A new column – `CREATE TABLE IF NOT EXISTS` does not add it
On the Video 59 volume (2 courses) I ran `CREATE TABLE IF NOT EXISTS courses (…, description text)`:
`NOTICE: relation "courses" already exists, skipping` – the columns stayed `id, title, created_at`.
`IF NOT EXISTS` looks at the **table name** only. So `app/db.py` now has a second statement:
```sql
ALTER TABLE courses ADD COLUMN IF NOT EXISTS description text;
```
New image, `docker compose up -d api` (1.73 s): `\d courses` shows `description | text`, the two old courses are there with
`"description": null`, and `POST {"title": "Alembic", "description": "Migrations in production"}` → id 3.
`CourseIn` got `description: str | None = Field(default=None, max_length=500)`; `tests/test_homework59.py` builds the
**old** table, opens the app's `Database` and checks that the column is added and the row kept.

This works for one column. For the tenth change – a rename, a NOT NULL, an index, a data fix – you want a history of
changes that runs in order, once, everywhere: **Alembic** (Video 60).

