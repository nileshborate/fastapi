# 21 – Background Tasks and Lifespan Events

**FastAPI Mastery: Zero to Production** – Video 21 · Nilesh Technology

**Background tasks** run small jobs *after* the response is sent, so the client doesn't wait.
The **lifespan** runs code once when the app **starts** and once when it **stops**.

## What's new
```
21-background-tasks-lifespan/
├── app/
│   ├── tasks.py          # NEW: write_log, send_welcome_email  (plain functions)
│   ├── main.py           # NEW: lifespan (startup + shutdown) · TrustedHostMiddleware
│   ├── middleware.py     # homework: security_headers, limit_upload_size (413)
│   ├── dependencies.py   # NEW: audit_log - a background task from a dependency
│   ├── routers/students.py   # POST /students sends a welcome email in the background
│   └── services/course_service.py   # NEW: load_courses(path)
├── data/courses.json     # NEW: 3 starter courses, loaded at startup
└── tests/test_background.py · tests/test_lifespan.py
```

## Run it
```bash
cd 21-background-tasks-lifespan
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env  - then set API_KEY
fastapi dev app/main.py         # "Startup: loaded 3 courses from data/courses.json"
pytest -v                       # 39 passed
```
POST a student in `/docs`: the response comes back at once, and 3 seconds later the terminal prints
`welcome email sent to ...` (also written to `app.log`). Stop the server with **Ctrl+C** to see the shutdown message.

## Background tasks
```python
@router.post("/students", status_code=201)
def create_student(data: StudentCreate, background_tasks: BackgroundTasks, settings: SettingsDep) -> StudentOut:
    student = student_service.create_student(data)
    background_tasks.add_task(send_welcome_email, student.name, student.email, settings.log_file, settings.email_delay_seconds)
    return student          # sent right away - the task runs after
```
- `add_task(function, *args)` – pass the function itself (no brackets) and its arguments.
- A normal `def` task runs in a thread pool; an `async def` task runs on the event loop (don't block it).
- Dependencies can add tasks too (`audit_log`): it's the same task list.
- Tasks run **in the same process**, after the response. If the server stops, unfinished tasks are lost.
  For heavy, long or must-not-be-lost jobs use a real **task queue**: Celery, RQ, ARQ, Dramatiq (with Redis/RabbitMQ).

## Lifespan
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.started_at = time.time()        # STARTUP - once, before the first request
    course_service.load_courses(settings.seed_file)
    yield                                     # the app answers requests here
    course_service.COURSES.clear()            # SHUTDOWN - once, when the server stops

app = FastAPI(lifespan=lifespan)
```
- Use it for things you create once: database engines, HTTP clients, ML models, caches.
- `@app.on_event("startup")` is the **old, deprecated** way.
- `TestClient(app)` runs the lifespan only inside `with TestClient(app) as client:`.

## Interview questions
1. **What are background tasks in FastAPI and when do you use them?** Functions added with `background_tasks.add_task(...)` that run after the response is sent – in the same process. Good for small jobs the client shouldn't wait for: sending an email, writing a log, a notification.
2. **BackgroundTasks or Celery?** BackgroundTasks: small, quick jobs, no extra infrastructure, but no retries and lost if the server stops. Celery (or RQ/ARQ): a separate worker and a broker like Redis – for heavy, long, scheduled or must-not-be-lost jobs, with retries and scaling.
3. **What is the lifespan and why use it instead of `on_event`?** An async context manager passed to `FastAPI(lifespan=...)`: code before `yield` runs once at startup, code after `yield` runs once at shutdown. It keeps setup and cleanup together (like a yield dependency), can share objects through `app.state`, and replaces the deprecated `on_event` handlers.

## Homework
1. When a course is created (`POST /courses`), add a background task that writes `course created: <title>` to the log.
2. In the lifespan: if the seed file does not exist, print a warning and start with empty data – don't crash.
3. At shutdown, save all courses to a backup JSON file (`backup_file` in settings), before clearing them.
4. Tests for each.

Answer at the start of Video 22.

## Homework answer
The full code is in [22-databases-orms](../22-databases-orms) (`app/routers/courses.py`, `app/main.py`, `app/services/course_service.py`, tests).
```python
# 1. routers/courses.py - a background task when a course is created
course = course_service.create_course(data)
background_tasks.add_task(write_log, f"course created: {course.title}", settings.log_file)

# 2. + 3. main.py - lifespan
if config.load_seed_data:
    if config.seed_file.exists():
        count = course_service.load_courses(config.seed_file)
    else:
        print(f"Warning: {config.seed_file} not found - starting with empty data")
yield
saved = course_service.save_courses(config.backup_file)     # save BEFORE clearing
course_service.COURSES.clear()

# services/course_service.py
def save_courses(path: Path) -> int:
    rows = [course.model_dump(exclude={"id"}) for course in COURSES.values()]
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return len(rows)
```
- New setting `backup_file: Path = Path("data/backup_courses.json")` (in `.gitignore`).
- Tests: `test_course_created_is_logged`, `test_missing_seed_file_does_not_crash` (uses `capsys` to read what was printed), `test_shutdown_saves_a_backup`.
