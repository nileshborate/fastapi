# 33 – Async Database Part 1: async def, AsyncSession & an Async Driver

**FastAPI Mastery: Zero to Production** – Video 33 · Nilesh Technology

Until now every endpoint was `def` and every database call blocked a thread while it waited.
Today the whole path becomes **async**: an async driver, an async engine, `AsyncSession`, `async def`
endpoints with `await` – and the one trap that catches everybody: **lazy loading** (`MissingGreenlet`).

## The project (fresh and small)
```
33-async-db-part1/
├── alembic/                 # alembic init -t async alembic  ->  env.py runs migrations with asyncio
├── app/
│   ├── database.py          # create_async_engine · async_sessionmaker · AsyncSession · async get_db
│   ├── models/              # Teacher 1 - N Course
│   └── routers/             # async def + await
├── demos/lazy_load.py       # python -m demos.lazy_load - the trap and two fixes
└── tests/                   # test_api.py (TestClient) · test_async_session.py (async tests)  - 7 tests
```

## Run it
```bash
cd 33-async-db-part1
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
alembic upgrade head
fastapi dev app/main.py
python -m demos.lazy_load
pytest -v                       # 7 passed (on PostgreSQL + asyncpg too)
```

## Sync vs async – what changes
| | Sync (Videos 22–32) | Async (today) |
|---|---|---|
| URL | `sqlite:///` · `postgresql+psycopg://` | `sqlite+aiosqlite:///` · `postgresql+asyncpg://` |
| Engine | `create_engine(url)` | `create_async_engine(url)` |
| Session | `sessionmaker(bind=engine)` → `Session` | `async_sessionmaker(engine, expire_on_commit=False)` → `AsyncSession` |
| get_db | `with SessionLocal() as db: yield db` | `async with SessionLocal() as db: yield db` |
| Endpoint | `def` (runs in a thread pool) | `async def` (runs on the event loop) |
| Query | `db.scalars(stmt)` | `await db.scalars(stmt)` |
| Get / commit / refresh | `db.get` · `db.commit()` | `await db.get` · `await db.commit()` |
| Add | `db.add(obj)` | `db.add(obj)` – **no await**: it only remembers the object |
| Shutdown | `engine.dispose()` | `await engine.dispose()` |

## The trap: lazy loading
```python
course = await db.scalar(select(Course))
course.teacher        # MissingGreenlet: greenlet_spawn has not been called - a HIDDEN query

# fix 1: load it in the same await
await db.scalar(select(Course).options(selectinload(Course.teacher)))
# fix 2: load it later, with an await (Base needs the AsyncAttrs mixin)
teacher = await course.awaitable_attrs.teacher
```
In an endpoint the same mistake is a **500** (`ResponseValidationError`): Pydantic reads `course.teacher`
while building the answer. And `expire_on_commit=True` breaks it too – after `commit` every attribute
would need a new query.

## Interview questions
1. **When does an async database driver actually help?** When requests spend time *waiting* (database, network). While one request awaits the database, the event loop serves others. It does not make a single query faster, and CPU-heavy work gains nothing.
2. **Why do you get `MissingGreenlet`, and how do you fix it?** Code touched a not-loaded relationship (or an expired attribute), so SQLAlchemy tried to run a query without `await`. Load relationships up front (`selectinload`), use `awaitable_attrs`, and set `expire_on_commit=False`.
3. **`def` or `async def` for an endpoint?** `async def` when everything inside is awaitable (an async driver, `httpx.AsyncClient`). A blocking call inside `async def` (a sync driver, `time.sleep`, `requests`) blocks the whole event loop – then plain `def` is better: FastAPI runs it in a thread pool.

## Homework
1. `GET /teachers/{teacher_id}` – the teacher **with** their courses (`TeacherDetail`), async, with `selectinload` – and 404.
2. `PATCH /courses/{course_id}` `{"fee": 349}` – async: `await db.get`, change, `await db.commit()`; 404 for an unknown course.
3. An async test that reads a teacher's courses with `awaitable_attrs`.

Answer at the start of Video 34 (Async Database Part 2).
