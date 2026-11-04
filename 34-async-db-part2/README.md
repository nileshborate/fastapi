# 34 – Async Database Part 2: gather, Sync vs Async Measured, Blocking Code

**Video 34** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (teachers + courses, async, Alembic). New today:
- `asyncio.gather` – four queries **at the same time**, each with its **own** `AsyncSession`
- why **one** session can't serve two tasks (`concurrent operations are not permitted`)
- **measured**: `def` vs `async def` vs blocking code inside `async def`
- code that **can't** be async: `run_in_threadpool` (or `asyncio.to_thread`)
- `lazy="raise"` – a forgotten `selectinload` fails loudly
- the **connection pool**: `pool_size`, `max_overflow`, `pool_timeout`, `pool_pre_ping`
- async tests with `httpx.AsyncClient` + `ASGITransport`

## Run it
```bash
cd 34-async-db-part2
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
fastapi dev app/main.py           # http://127.0.0.1:8000/docs
python -m demos.gather            # one by one vs gather, one session vs own sessions
python -m demos.benchmark         # 50 requests at once against 4 endpoints
python -m demos.pool              # a tiny pool: 2 + 1 connections, the 4th waits -> timeout
pytest                            # 9 passed (SQLite and PostgreSQL)
```

## Project
```
app/
  config.py        DATABASE_URL + POOL_SIZE, MAX_OVERFLOW, POOL_TIMEOUT
  database.py      create_async_engine(..., pool_size, max_overflow, pool_timeout, pool_pre_ping)
  models/          Teacher 1-N Course - relationships with lazy="raise"
  schemas.py       ... + Stats
  routers/
    school.py      POST /teachers, GET/POST /courses
    stats.py       GET /stats  - asyncio.gather, one session per task
    bench.py       /bench/sync, /bench/async, /bench/blocking, /bench/threadpool
demos/  gather.py, benchmark.py, pool.py
tests/  conftest.py (httpx.AsyncClient), test_stats.py, test_bench.py
```

## asyncio.gather – one session per task
```python
async def count_courses() -> int:
    async with SessionLocal() as db:            # its own session = its own connection
        return await db.scalar(select(func.count()).select_from(Course))

teachers, courses, avg_fee, top = await asyncio.gather(
    count_teachers(), count_courses(), average_fee(), top_courses()
)
```
One `AsyncSession` shared by two tasks → `InvalidRequestError: This session is provisioning a new
connection; concurrent operations are not permitted`. A session is **one** conversation with the database.

## Measured (`python -m demos.benchmark`, 50 requests at once, each waits 0.1 s)
| Endpoint | How it waits | Time |
|---|---|---|
| `/bench/sync` | `def` + `time.sleep` → thread pool (40 threads) | ~0.25 s |
| `/bench/async` | `async def` + `await asyncio.sleep` | ~0.1 s |
| `/bench/blocking` | `async def` + `time.sleep` – **blocks the event loop** | ~5.05 s |
| `/bench/threadpool` | `async def` + `await run_in_threadpool(sync_fn)` | ~0.24 s |

## Code that can't be async
```python
from fastapi.concurrency import run_in_threadpool
report = await run_in_threadpool(slow_report)      # a sync library call, in a thread
# or: await asyncio.to_thread(slow_report)
```
CPU-heavy work (big PDFs, image resizing) doesn't belong in a request at all – a background worker (later).

## The pool
| Setting | Default | Meaning |
|---|---|---|
| `pool_size` | 5 | connections kept open |
| `max_overflow` | 10 | extra connections when it's busy |
| `pool_timeout` | 30 | seconds to wait for a free one → `TimeoutError` (QueuePool limit … reached) |
| `pool_pre_ping` | False | test the connection first – survives a database restart |

## Interview questions
1. **What does `asyncio.gather` do, and what must you watch with a database?** It starts several coroutines at once and waits for all; results come back in the same order. Every task needs its **own** `AsyncSession` – one session can't run two things at once.
2. **What happens if you call blocking code inside `async def`?** It blocks the event loop – every other request waits (50 × 0.1 s = 5 s). Use the async version, a plain `def` endpoint, or `run_in_threadpool` / `asyncio.to_thread`.
3. **What are `pool_size` and `max_overflow`?** `pool_size` connections stay open; under load up to `max_overflow` more are opened. When all are busy, a request waits `pool_timeout` seconds, then fails. Total across all app workers must stay below the database's `max_connections`.

## Homework
1. `GET /teachers/{teacher_id}/summary` – the teacher's name, number of courses and total fees, loaded with `asyncio.gather` (each query its own session); 404 for an unknown teacher.
2. `GET /bench/report` – call a sync function `make_report()` that takes 0.2 s **without** blocking the event loop.
3. A test: 20 requests to `/bench/report` at once must finish in well under 20 × 0.2 s.

Answer at the start of Video 35 (Clean Architecture: Repository and Service Layers).
