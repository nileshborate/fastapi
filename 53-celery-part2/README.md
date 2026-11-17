# 53 – Background Jobs with Celery, Part 2: retries, schedules, workflows, monitoring

**Video 53** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project with a **flaky email server** (it fails twice per address, then works).
Celery **retries** only the temporary errors, with **exponential backoff** (1 s, 2 s, 4 s) and a limit;
**celery beat** sends tasks on a **schedule** (every 5 s, every day at 07:30, every Monday);
a **chain** runs tasks one after another and a **chord** runs them in parallel and combines the
results (1.5 s of work in 0.56 s); and you **watch** the workers with `inspect`, a `/workers`
endpoint and the **Flower** dashboard.

## Run it
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
cd 53-celery-part2
pip install -r requirements.txt

celery -A app.celery_app worker --loglevel=info --pool=threads --concurrency=4   # terminal 1
celery -A app.celery_app beat --loglevel=info                                     # terminal 2
celery -A app.celery_app flower                       # terminal 3 -> http://localhost:5555
fastapi dev app/main.py                                                           # terminal 4

python -m demos.retry       # RETRY 0.27 s · 1.48 s -> SUCCESS 3.67 s · bounce: FAILURE at once · down: gives up
python -m demos.canvas      # chain: 3 x 0.5 s = 1.57 s · chord: 3 in parallel = 0.56 s · course 9 -> 404
python -m demos.schedule    # beat: heartbeat every 5 s -> 3 heartbeats in 16 s
python -m demos.watch       # GET /workers: 503 without a worker · 200 + the active task with one
pytest                      # 8 passed (eager mode)
```
(For Flower to show tasks, start the worker with `-E` – task events.)

## Project
```
app/
  email_server.py      a flaky server: EmailServerDown (temporary) · ValueError (permanent)
  celery_app.py        timezone="Asia/Kolkata" · beat_schedule: 5.0 s · crontab(hour=7, minute=30) · Mondays
  tasks.py             send_email (autoretry_for, retry_backoff, max_retries) · load_course · make_report
                       · notify · summarize · heartbeat · daily_digest
  routers/jobs.py      POST /emails · POST /reports/{id}/pipeline (chain) · POST /reports/summary (chord)
                       · GET /tasks/{id}
  routers/workers.py   GET /workers -> celery_app.control.inspect().active()  (503 = no worker)
demos/   retry · canvas · schedule · watch   tests/   conftest (eager) · test_part2
```

## Retries
```python
@celery_app.task(bind=True,
                 autoretry_for=(EmailServerDown,),   # ONLY temporary errors
                 retry_backoff=1, retry_backoff_max=30, retry_jitter=False,
                 max_retries=3)                      # 1 try + 3 retries
```
| demos.retry | |
|---|---|
| `asha@` (fails 2x) | RETRY 0.27 s → RETRY 1.48 s → **SUCCESS 3.67 s**, attempts 3 |
| `bounce@` (`ValueError`) | **FAILURE** at once – not in `autoretry_for` |
| `down@` (always down) | waits 1 s, 2 s, 4 s → **FAILURE** at 7.86 s after 4 attempts |

A retried task runs **again** – make it **idempotent** (safe to run twice), e.g. remember "email X sent".

## Canvas
| | runs | result |
|---|---|---|
| `chain(a.s(x), b.s(), c.s(email))` | one after another, each result → the next task | 1.57 s (3 × 0.5 s) |
| `group(a.s(1), a.s(2), a.s(3))` | in parallel | a list of results |
| `chord(group(...), summarize.s())` | a group, then ONE callback with all results | 0.56 s for 3 × 0.5 s |
`.s()` = a **signature**: a task + its arguments, not called yet.

## Beat
celery beat is a **clock**: it only **sends** tasks at the right time – a worker still runs them.
Run **exactly one** beat (two beats = every task twice). `crontab(hour=7, minute=30)` uses the app's
`timezone`.

## Watching workers
- `celery_app.control.inspect().active()` / `.stats()` / `.registered()` – ask every worker, `None` if nobody answers.
- `GET /workers` → 200 with the busy tasks, **503** when no worker is alive (a health check).
- **Flower** (`celery -A app.celery_app flower`): workers, every task with state, runtime, retries and errors.

## Rules
- Retry **temporary** errors only (timeouts, 503s); fail fast on permanent ones (bad data).
- Always **back off** and set a **limit** – an endless retry loop hurts the server you depend on.
- Tasks must be **idempotent** – retries and redeliveries run them again.
- One beat process. Many workers are fine.
- Use a chord for "do many in parallel, then combine" – never wait for a task **inside** a task.

## Interview questions
1. **How do you make Celery tasks reliable when an external service fails?** Retry only temporary errors (`autoretry_for`), with exponential backoff, jitter and `max_retries`, and fail fast on permanent errors. Make the task idempotent, because a retried task runs again.
2. **What is celery beat and how is it different from a worker?** Beat is a scheduler: it sends tasks to the queue at fixed intervals or crontab times. Workers execute tasks. You run exactly one beat and as many workers as you need.
3. **What are chain, group and chord in Celery?** A chain runs tasks one after another, passing each result to the next. A group runs tasks in parallel. A chord is a group plus a callback that receives all results once every task in the group is done.

## Homework
1. **Idempotent emails:** `send_email` must not send twice – before sending, `SET sent:<to> 1 NX EX 3600` in Redis; if it already exists, return `{"to": ..., "skipped": True}`.
2. **A nightly cleanup:** a beat entry `cleanup-2-am` → task `cleanup()` at 02:00 that returns how many `heartbeats` it deleted.
3. Tests for both.

Answer at the start of Video 54 (API Versioning).
