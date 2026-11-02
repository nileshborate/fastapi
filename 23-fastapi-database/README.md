# 23 – Connecting FastAPI to a Database

**FastAPI Mastery: Zero to Production** – Video 23 · Nilesh Technology

Our courses now live in a real database – SQLite on your computer, PostgreSQL with one line of change.
Restart the server: the courses are still there.

## What's new
```
23-fastapi-database/
├── app/
│   ├── database.py          # NEW: engine · SessionLocal · Base · get_db
│   ├── models/course.py     # NEW: the courses TABLE (SQLAlchemy model)
│   ├── services/course_service.py   # now uses a session: select, get, add, commit, delete
│   ├── routers/courses.py   # db: DBSession  ·  response_model=CourseOut
│   ├── schemas/course.py    # CourseOut: from_attributes=True
│   └── main.py              # lifespan: create_all + seed once + engine.dispose()
├── db_basics/               # homework answer (Video 22)
└── tests/test_database.py   # + every test gets a clean database
```

## Run it
```bash
cd 23-fastapi-database
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env  - then set API_KEY
fastapi dev app/main.py         # creates coursehub.db + 3 starter courses
pytest -v                       # 55 passed
```
Set `DB_ECHO=true` in `.env` to see every SQL statement in the terminal.

## The pieces
```python
engine = create_engine(settings.database_url, echo=settings.db_echo)   # ONE per app: the connections
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def get_db() -> Iterator[Session]:      # ONE session per request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBSession = Annotated[Session, Depends(get_db)]
```
- **Engine**: knows the database URL and keeps a pool of connections. Create it once.
- **Session**: one unit of work – add, query, commit. One per request, always closed.
- **Model** (`app/models`) = a table. **Schema** (`app/schemas`) = what the API sends and receives.
  `from_attributes=True` lets `CourseOut` read a `Course` object.
- `Base.metadata.create_all()` creates missing tables – fine for now; **Alembic** migrations come later.

## PostgreSQL
```bash
docker run --name coursehub-db -e POSTGRES_USER=coursehub -e POSTGRES_PASSWORD=coursehub \
  -e POSTGRES_DB=coursehub -p 5432:5432 -d postgres:16
pip install "psycopg[binary]"
```
`.env`:  `DATABASE_URL=postgresql+psycopg://coursehub:coursehub@localhost:5432/coursehub`
Nothing else changes – the health endpoint now says `"database": "postgresql"`.

## Interview questions
1. **How do you connect FastAPI to a database with SQLAlchemy?** Create one engine from the database URL, a `sessionmaker` (SessionLocal), and a `get_db` dependency with `yield` that opens a session per request and closes it in `finally`. Endpoints get it with `Depends(get_db)` (an `Annotated` alias like `DBSession`).
2. **Why one session per request, and why close it?** A session is a unit of work with its own transaction and identity map; sharing it between requests mixes their changes and isn't thread-safe. Closing returns the connection to the pool – otherwise you leak connections until the pool runs out.
3. **What is the difference between a SQLAlchemy model and a Pydantic schema?** The model describes a database table and is used to read and write rows. The schema describes the data the API accepts and returns, with validation. Keeping them separate lets the table change without changing the API (and hides internal columns); `from_attributes=True` converts a model into a schema.

## Homework
1. Move **students** to the database: a `Student` model (unique email), the student service with a session, `StudentOut` with `from_attributes=True`.
2. `GET /admin/db`: the database name (`engine.dialect.name`) and the table names (`sqlalchemy.inspect(engine).get_table_names()`).
3. `POST /courses` with a title that already exists crashes with `IntegrityError` – catch it, `rollback()`, and return **409 Conflict**.
4. Tests for each.

Answer at the start of Video 24.
