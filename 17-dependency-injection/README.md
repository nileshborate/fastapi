# 17 – Dependency Injection Basics

**FastAPI Mastery: Zero to Production** – Video 17 · Nilesh Technology

Stop copying the same code into every endpoint. Write it **once** as a dependency, and let FastAPI call it with `Depends()`.

## What's new in this project
```
app/
├── dependencies.py      # NEW: pagination, verify_api_key, get_course_or_404 + type aliases
├── routers/
│   ├── courses.py       # uses Pagination, CourseDep, dependencies=[Depends(verify_api_key)]
│   ├── students.py
│   └── teachers.py      # homework answer from Video 16
├── schemas/  (course, student, teacher)
└── services/ (course_service, student_service, teacher_service)
tests/
├── conftest.py          # client fixture + clears app.dependency_overrides
├── test_courses.py      # 6 tests, incl. dependency_overrides
├── test_students.py
└── test_teachers.py     # homework answer from Video 16
```

## Run it
```bash
cd 17-dependency-injection
pip install -r requirements.txt
fastapi dev app/main.py     # http://127.0.0.1:8000/docs
pytest -v                   # 10 passed
```
API key for the demo: `X-API-Key: learn-fastapi-123`

## Three kinds of dependencies
| Dependency | What it does | How we use it |
|------------|--------------|---------------|
| `pagination(skip, limit)` | shared query parameters | `page: Pagination` |
| `verify_api_key(x_api_key)` | a check – raises 401 | `dependencies=[Depends(verify_api_key)]` (no value needed) |
| `get_course_or_404(course_id)` | loads an object or raises 404 | `course: CourseDep` |

```python
Pagination = Annotated[dict[str, int], Depends(pagination)]   # type + where the value comes from
```

## Testing: replace a dependency
```python
app.dependency_overrides[verify_api_key] = lambda: None   # skip the key check in this test
app.dependency_overrides.clear()                          # undo it
```

## Interview questions
1. **What is dependency injection in FastAPI, and why use it?** You declare what an endpoint needs with `Depends(some_function)`; FastAPI calls the function (resolving its own query, path, header or body parameters), and passes the result in. Shared logic is written once, endpoints stay short, the docs include the dependency's parameters, and dependencies can be replaced in tests.
2. **Parameter dependency vs `dependencies=[...]` in the decorator?** As a parameter, you receive the return value (`page: Pagination`). In `dependencies=[Depends(...)]` the dependency still runs – and can raise errors – but its value is ignored. Use it for checks like an API key.
3. **How do you replace a dependency in tests?** `app.dependency_overrides[original] = replacement` – FastAPI calls the replacement instead. Clear it after the test with `app.dependency_overrides.clear()`.

## Homework
1. Create `get_student_or_404` + `StudentDep`, and use it in `GET /students/{student_id}`.
2. Create `require_admin(x_role: Header)` → 403 if the value isn't `"admin"`. Add it to `DELETE /courses/{course_id}` next to `verify_api_key`.
3. Add `Pagination` to `GET /teachers`.
4. Write a test that overrides `require_admin`.

Answer at the start of Video 18.

## Homework answer
The answer is inside the next project, [`../18-advanced-dependencies`](../18-advanced-dependencies): `get_student_or_404` + `StudentDep` (used in `GET /students/{student_id}`), `require_admin` returning 403 on `DELETE /courses/{course_id}` (in Video 18 it reads the role through the `get_role` sub-dependency), `Pagination` on `GET /teachers`, and `test_override_require_admin` in `tests/test_courses.py`.
