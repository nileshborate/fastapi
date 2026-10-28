# 18 – Advanced Dependencies

**FastAPI Mastery: Zero to Production** – Video 18 · Nilesh Technology

Classes as dependencies, dependencies that use other dependencies, `yield` for setup + cleanup, and dependencies for a whole router.

## What's new
```
app/
├── dependencies.py      # PaginationParams (class) · get_role → require_admin (sub-dependency)
│                        # RoleChecker (callable class) · get_db (yield) · StudentDep (homework)
└── routers/
    └── admin.py         # NEW: APIRouter(dependencies=[...]) - every endpoint protected
tests/test_admin.py      # router-level deps, yield cleanup, caching
```

## Run it
```bash
cd 18-advanced-dependencies
pip install -r requirements.txt
fastapi dev app/main.py     # http://127.0.0.1:8000/docs
pytest -v                   # 11 passed
```
Headers for the demo: `X-API-Key: learn-fastapi-123` and `X-Role: admin` (or `teacher`; default `student`).

## The four techniques
| Technique | Code | Why |
|-----------|------|-----|
| Class dependency | `Pagination = Annotated[PaginationParams, Depends()]` | `page.skip` with autocomplete; `Depends()` with no argument uses the type |
| Sub-dependency | `def require_admin(role: CurrentRole)` | build checks from small pieces; `get_role` runs **once** per request (cached) |
| Callable instance | `allow_staff = RoleChecker(["admin", "teacher"])` | a dependency with its own settings |
| `yield` dependency | `db = FakeSession(); try: yield db; finally: db.close()` | setup before, cleanup after – even after an error |
| Router-level | `APIRouter(dependencies=[Depends(verify_api_key), Depends(require_admin)])` | protect every endpoint of a router |

App-wide: `FastAPI(dependencies=[...])` runs a dependency for **every** endpoint.

## Interview questions
1. **How does a dependency with `yield` work?** The code before `yield` runs before the endpoint; the yielded value is injected; the code after `yield` (put it in `finally`) runs after the endpoint, even if it raised an error. It's the standard way to open and close a database session.
2. **What are sub-dependencies, and are they called twice?** A dependency can declare its own dependencies with `Depends`. FastAPI resolves the whole tree. If the same dependency appears more than once in one request, it is called once and the result is reused (`use_cache=True` by default).
3. **How do you protect all endpoints of a router?** `APIRouter(dependencies=[Depends(check)])` – or `app.include_router(router, dependencies=[...])` – runs the check for every endpoint in it. `FastAPI(dependencies=[...])` does it for the whole app.

## Homework
1. Turn `CourseFilter` into a **class dependency**: `min_price: float | None` and `max_price: float | None` query parameters (both ≥ 0), used by `GET /courses`.
2. Create `allow_teachers = RoleChecker(["admin", "teacher"])` and protect **all** of `/teachers` with router-level dependencies.
3. Write a `yield` dependency `request_timer` that records the start time, yields, and prints how long the request took. Add it app-wide.
4. One test for each.

Answer at the start of Video 19.
