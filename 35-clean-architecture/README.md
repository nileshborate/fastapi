# 35 – Clean Architecture: Repository and Service Layers

**Video 35** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (teachers + courses, async, Alembic) – split into **layers**:

```
HTTP request
   │
   ▼
routers/        HTTP only: read the request, call the service, return the answer
   │
   ▼
services/       the business rules: plain Python, no SQL, no HTTP
   │
   ▼
uow.py          Unit of Work: ONE session, all repositories, ONE commit (or rollback)
   │
   ▼
repositories/   ALL the SQL for one model - nothing else
   │
   ▼
database
```

## Run it
```bash
cd 35-clean-architecture
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
fastapi dev app/main.py              # http://127.0.0.1:8000/docs
python -m demos.sqlmodel_demo        # SQLModel: one class = table + schema
pytest                               # 11 passed (SQLite and PostgreSQL)
```

## Project
```
app/
  config.py           + MAX_COURSES_PER_TEACHER (a business rule, in one place)
  database.py         engine · SessionLocal · Base
  errors.py           NEW: DomainError -> NotFoundError 404 · ConflictError 409 · RuleError 422
  repositories/       NEW: courses.py · teachers.py  - get, list, add, get_by_title, count_for_teacher
  uow.py              NEW: UnitOfWork + get_uow (IntegrityError -> ConflictError)
  services/           NEW: courses.py (create, transfer, the rules) · teachers.py
  routers/            courses.py · teachers.py - thin
  main.py             ONE exception handler: DomainError -> {"detail": ...}
demos/sqlmodel_demo.py
tests/
  fakes.py            NEW: FakeCourseRepository · FakeTeacherRepository · FakeUnitOfWork
  test_service.py     unit tests with fakes - no database (0.02 s)
  test_uow.py         the unit of work on a real database
  test_api.py         all layers together
```

## The business rules (services/courses.py)
- the teacher must exist → `NotFoundError` (404)
- the title must be new → `ConflictError` (409)
- a teacher teaches at most 3 courses → `RuleError` (422)
- transfer: not to the same teacher → `RuleError` (422)

```python
async def create(self, data: CourseCreate) -> Course:
    teacher = await self._teacher_with_room(data.teacher_id)
    if await self.uow.courses.get_by_title(data.title) is not None:
        raise ConflictError("Course title already exists")
    course = Course(title=data.title, fee=data.fee, teacher=teacher)
    self.uow.courses.add(course)
    await self.uow.commit()
    return course
```

## Why?
| Before (one fat router) | After (layers) |
|---|---|
| SQL, rules and HTTP in one function | each layer has ONE job |
| testing a rule needs a database + HTTP | rules tested with fakes – milliseconds |
| `HTTPException` deep in the logic | domain errors → one handler |
| the same query copied into many routers | one repository method |

## SQLModel (an overview)
One class can be a table **and** a Pydantic schema (`table=True`). Less code – but a
`table=True` class does **not** validate (`Course(fee=-5)` works!). Validate with a schema class
(`CourseCreate`), then `Course.model_validate(data)`. This course keeps SQLAlchemy + Pydantic.

## Interview questions
1. **What is the repository pattern?** A class that holds all database access for one model (get, list, add …). The rest of the app calls methods, never writes SQL. Swap the database or test with a fake – the callers don't change.
2. **What is a unit of work?** One object that owns the session, gives all repositories that session, and decides at the end: one commit, or a rollback. Many changes – one transaction.
3. **Why a service layer, and what goes into it?** The business rules – in plain Python, without HTTP or SQL. Routers stay thin, rules are reusable (API, CLI, jobs) and testable with fakes.

## Homework
1. `PATCH /courses/{course_id}/fee` `{"fee": 349}` – in the **service**: a fee may go up at most 50 % at once (`RuleError`), 404 for an unknown course.
2. `DELETE /teachers/{teacher_id}` – only when the teacher has no courses (`RuleError`), 404 otherwise. Add `delete` to the repository.
3. Unit tests with the fakes for both rules – no database.

Answer at the start of Video 36 (Security Fundamentals).

## Homework answer (shown at the start of Video 36)
```python
# services/courses.py - the rule lives in the SERVICE
async def change_fee(self, course_id: int, fee: int) -> Course:
    course = await self.get(course_id)                  # NotFoundError -> 404
    if fee > course.fee * 1.5:                          # at most +50 % at once
        raise RuleError("A fee may go up at most 50% at once")
    course.fee = fee
    await self.uow.commit()
    return course

# services/teachers.py
async def delete(self, teacher_id: int) -> None:
    teacher = await self.uow.teachers.get(teacher_id)   # None -> NotFoundError
    if await self.uow.courses.count_for_teacher(teacher_id) > 0:
        raise RuleError("The teacher still has courses")
    await self.uow.teachers.delete(teacher)             # NEW repository method
    await self.uow.commit()
```
`PATCH /courses/{course_id}/fee` and `DELETE /teachers/{teacher_id}` (204) – one line each in the
routers. `FakeTeacherRepository` got `delete` too. `tests/test_homework35.py`: both rules with the
fakes + one API test. `pytest` → **14 passed** (SQLite and PostgreSQL).
