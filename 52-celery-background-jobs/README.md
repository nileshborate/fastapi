# 52 – Background Jobs with Celery, Part 1

**Video 52** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project: slow work (a 2-second email, a 5-step report) moves **out of the request**
into a **Celery worker** – a separate process. Redis is the **broker** (the queue where tasks wait)
and the **result backend** (states and results). Registration goes from **2.02 s to 0.03 s**,
a report answers **202 Accepted** with a `Location` to poll, the worker reports **progress**, and
tasks sent while no worker runs simply **wait in Redis** – nothing is lost.

## Run it
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
cd 52-celery-background-jobs
pip install -r requirements.txt

# terminal 1 - the worker
celery -A app.celery_app worker --loglevel=info --pool=solo     # solo: works on Windows too
# terminal 2 - the API
fastapi dev app/main.py

python -m demos.inline      # register: email in the request 2.02 s · as a task 0.03 s · STARTED -> SUCCESS
python -m demos.report      # 202 + Location · PROGRESS 1..5 of 5 · SUCCESS · course 99 -> FAILURE
python -m demos.queue       # no worker: 3 tasks wait (LLEN celery = 3) · start it: one by one
pytest                      # 6 passed (eager mode - no Redis, no worker)
```
(The demos start their own server on port 8052 and their own worker – its log goes to `worker.log`.)

## Project
```
app/
  config.py          broker_url (redis/0) · result_backend (redis/1) · email_seconds · report_step_seconds
  celery_app.py      Celery("course_hub", broker=..., backend=..., include=["app.tasks"]) + JSON config
  tasks.py           @celery_app.task send_welcome_email · @celery_app.task(bind=True) build_report
  routers/users.py   POST /users/register-slow (email inline) · POST /users/register (.delay)
  routers/reports.py POST /reports/{course_id} -> 202 + Location: /tasks/{id}
  routers/tasks.py   GET /tasks/{task_id} -> AsyncResult: state · progress · result · error
demos/   inline · report · queue    tests/   conftest (eager) · test_jobs
```

## How it fits together
```
FastAPI ── send_welcome_email.delay(email, name) ──> Redis db 0: list "celery"  (the queue)
                                                          │
                     celery worker (another process) <────┘  runs the function
                                                          │
FastAPI <── AsyncResult(id).state / .result ──── Redis db 1: celery-task-meta-<id>
```
States: **PENDING** (waiting – or unknown!) → **STARTED** (`task_track_started=True`) →
**PROGRESS** (our own, `self.update_state`) → **SUCCESS** / **FAILURE**.

| Measured | |
|---|---|
| `POST /users/register-slow` (email inside) | **2.02 s** |
| `POST /users/register` (`.delay`) | **0.03 s** – the email arrives ~2 s later |
| report, 5 steps of 0.5 s | PROGRESS 1..5 → SUCCESS at 2.66 s |
| 3 tasks, no worker | `LLEN celery` = 3, all PENDING – then done one by one |

## BackgroundTasks or Celery?
| | FastAPI `BackgroundTasks` | Celery |
|---|---|---|
| runs in | the same server process, after the response | a separate worker (other machines too) |
| server restarts | the job is lost | the task waits in Redis |
| status / result | none | `AsyncResult`: state, progress, result |
| setup | nothing | Redis + a worker process |
| use it for | tiny, quick, "nice to have" jobs | emails, reports, imports – work that matters |

## Rules
- Pass **simple JSON** arguments (ids, strings) – not ORM objects or sessions. The worker loads fresh data.
- Tasks are normal `def` functions, and they run in **another process** – no `request`, no FastAPI dependencies.
- `GET /tasks/{id}` is a `def` endpoint: `AsyncResult` does blocking Redis I/O → the threadpool (Video 48).
- **PENDING** also means "never heard of it" – validate ids, store task ids you created.
- Long work: **202 Accepted** + `Location`, and let the client poll (or push it: SSE, Video 49).
- On Windows run the worker with `--pool=solo` (the default prefork pool is not supported there).

## Interview questions
1. **Why use Celery instead of FastAPI's BackgroundTasks?** BackgroundTasks run inside the API process after the response: they share its CPU, have no status, and are lost if the server restarts. Celery runs tasks in separate worker processes fed by a broker, so jobs survive restarts, can scale across machines, report state and results, and can be retried.
2. **What are the broker and the result backend in Celery?** The broker is the message queue where tasks wait until a worker takes them (here a Redis list). The result backend stores each task's state and return value so the API can look them up by task id (here Redis keys `celery-task-meta-<id>`).
3. **How do you report the progress of a long-running task to the client?** Return 202 Accepted with a task id and a status URL. The task calls `self.update_state(state="PROGRESS", meta={...})` (with `bind=True`), and the status endpoint reads it with `AsyncResult(id).state` and `.info` – the client polls, or the server pushes updates with SSE or WebSockets.

## Homework
1. **A welcome-back email:** `POST /users/{email}/reminder` → 202, queues a new task `send_reminder(email)`; an unknown email → 404 (check `USERS` before queueing).
2. **A report for several courses:** `POST /reports?course_ids=1&course_ids=3` → one task that reports progress as `{"course": 1, "done": 1, "of": 2}`.
3. Tests for both (eager mode).

Answer at the start of Video 53 (Background Jobs with Celery, Part 2).
