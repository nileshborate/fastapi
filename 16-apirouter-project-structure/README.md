# 16 – APIRouter and Project Structure

**FastAPI Mastery: Zero to Production** – Video 16 · Nilesh Technology

One big `main.py` doesn't scale. We split the app into **routers**, **schemas** and **services** – the structure used in real FastAPI projects.

## Project structure
```
16-apirouter-project-structure/
├── app/
│   ├── __init__.py          # makes "app" a Python package
│   ├── main.py              # creates the FastAPI app + include_router(...)
│   ├── routers/             # HTTP layer: URLs, methods, status codes
│   │   ├── courses.py       # APIRouter(prefix="/courses", tags=["Courses"])
│   │   └── students.py
│   ├── schemas/             # Pydantic models: what goes IN and OUT
│   │   ├── course.py
│   │   └── student.py
│   └── services/            # business logic - plain Python, no FastAPI
│       ├── course_service.py
│       └── student_service.py
├── tests/
│   ├── conftest.py          # shared "client" fixture
│   ├── test_courses.py
│   └── test_students.py
├── homework_video15.py
└── requirements.txt
```
(`models/` for database tables comes in the database videos.)

## Run it
```bash
cd 16-apirouter-project-structure
pip install -r requirements.txt
fastapi dev app/main.py     # "Using import string: app.main:app"  ->  http://127.0.0.1:8000/docs
pytest -v                   # 8 passed (run from this folder)
```

## The request flow
`request → router (HTTP) → service (logic) → data`  ·  schemas validate what comes in and what goes out.

## APIRouter in 3 lines
```python
router = APIRouter(prefix="/courses", tags=["Courses"])   # routers/courses.py
@router.get("")                                           # -> GET /courses
app.include_router(courses.router)                        # main.py
```
- `prefix` must **not** end with `/`.
- `@router.get("")` = exactly the prefix (`/courses`); `@router.get("/")` would be `/courses/`.
- `tags` group the endpoints in `/docs`.
- Forget `include_router` → every route of that router is a **404**.

## Interview questions
1. **What is `APIRouter` and why use it?** A group of path operations, like a mini FastAPI app. You declare routes on it with the same decorators, then attach it with `app.include_router()`. It lets you split a big API into modules, with a shared prefix, tags, responses and (later) dependencies.
2. **What do `prefix` and `tags` do?** `prefix` is added in front of every path in the router (`/courses` + `/{course_id}`). `tags` group the endpoints in the OpenAPI docs. Neither changes your function code.
3. **How would you structure a FastAPI project?** By layers: `routers` for HTTP, `schemas` for Pydantic models, `services` for business logic, `models` for database tables, plus `core/config` for settings and `tests/`. Routers call services; services don't know about HTTP – so they are easy to test and reuse.

## Homework
Add a **teachers** module, following the same structure:
1. `app/schemas/teacher.py` – `TeacherCreate` (name, subject) and `TeacherOut` (id, name, subject).
2. `app/services/teacher_service.py` – `list_teachers`, `get_teacher`, `create_teacher`.
3. `app/routers/teachers.py` – `APIRouter(prefix="/teachers", tags=["Teachers"])`: GET list, GET one (404), POST (201).
4. Include it in `main.py`, and add `tests/test_teachers.py` with 2 tests.

Answer at the start of Video 17.
