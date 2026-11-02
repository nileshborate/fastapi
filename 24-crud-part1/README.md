# 24 – CRUD with the Database, Part 1: Create and Read

**FastAPI Mastery: Zero to Production** – Video 24 · Nilesh Technology

Courses, students **and** teachers now live in the database. Clean schemas (Base / Create / Out),
fields the database fills in (`id`, `created_at`), and clean errors: **404** and **409** from the service layer.

## What's new
```
24-crud-part1/
├── app/
│   ├── errors.py               # NEW: NotFoundError, AlreadyExistsError  (no HTTP inside)
│   ├── models/                 # course.py (+ created_at) · student.py · teacher.py
│   ├── schemas/                # XBase · XCreate (extra="forbid") · XOut (+ id, created_at)
│   ├── services/               # every service uses a session; raises domain errors
│   ├── routers/                # students: GET /students/by-email/{email}  ·  admin: GET /admin/db
│   └── main.py                 # exception handlers: NotFoundError -> 404, AlreadyExistsError -> 409
└── tests/test_crud.py
```

## Run it
```bash
cd 24-crud-part1
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env  - then set API_KEY
del coursehub.db                # IMPORTANT: create_all() does not add new columns to old tables
fastapi dev app/main.py
pytest -v                       # 65 passed
```

## Schemas: Base / Create / Out
```python
class CourseBase(BaseModel):            # what the client SENDS and SEES
    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)

class CourseCreate(CourseBase):         # input
    model_config = ConfigDict(extra="forbid")      # {"id": 500, ...} -> 422 extra_forbidden

class CourseOut(CourseBase):            # output: + what the DATABASE creates
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
```
`created_at: Mapped[datetime] = mapped_column(server_default=func.now())` – the database fills it, `db.refresh()` reads it back.

## Clean errors
```python
# services/course_service.py - no HTTP here
try:
    db.commit()
except IntegrityError:                  # the UNIQUE rule said no
    db.rollback()                       # the session is usable again
    raise AlreadyExistsError("Course title already exists") from None

# main.py - the ONE place that knows HTTP status codes
@app.exception_handler(AlreadyExistsError)
async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})
```

## Interview questions
1. **Why separate Create and Out schemas?** Input and output are different: the client must not send `id` or `created_at` (the database creates them), while the response must include them. A shared Base avoids repeating the common fields; `extra="forbid"` rejects unexpected input.
2. **How do you handle a unique-constraint violation with SQLAlchemy?** Catch `IntegrityError` on `commit()`, call `rollback()` so the session can be used again, and return **409 Conflict** – best via a domain error that an exception handler converts, so the service layer stays free of HTTP.
3. **What is the difference between `server_default` and `default` in SQLAlchemy?** `default` is computed by Python/SQLAlchemy when inserting; `server_default` becomes part of the table (`DEFAULT CURRENT_TIMESTAMP`) and is filled by the database – also for rows inserted by other tools. Read it back with `refresh()`.

## Homework
1. `GET /courses/by-title/{title}` – find a course by its unique title; 404 if missing.
2. Teachers get a unique `email` (model + schemas); a second teacher with the same email → **409** "Email already registered".
3. A `TeacherDep` dependency (like `CourseDep`) used by `GET /teachers/{teacher_id}`.
4. Tests for each.

Answer at the start of Video 25.

## Homework answer
The full code is in [25-crud-part2](../25-crud-part2) (`app/routers/courses.py`, `app/models/teacher.py`, `app/dependencies.py`, `tests/test_crud2.py`).
```python
# 1. GET /courses/by-title/{title}  - two path parts, so no conflict with /courses/{course_id}
def get_course_by_title(db: Session, title: str) -> Course:
    course = db.scalars(select(Course).where(Course.title == title)).first()
    if course is None:
        raise NotFoundError("Course")
    return course

# 2. teachers: a unique email -> 409
email: Mapped[str] = mapped_column(String(100), unique=True)       # model
email: EmailStr                                                     # TeacherBase
except IntegrityError:
    db.rollback()
    raise AlreadyExistsError("Email already registered") from None

# 3. TeacherDep
def get_teacher_or_404(teacher_id: int, db: DBSession) -> Teacher:
    return teacher_service.get_teacher(db, teacher_id)

TeacherDep = Annotated[Teacher, Depends(get_teacher_or_404)]
```
