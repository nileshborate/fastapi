# 25 – CRUD with the Database, Part 2: Update, Delete, Search & Sorting

**FastAPI Mastery: Zero to Production** – Video 25 · Nilesh Technology

The full CRUD for courses: **PUT** (replace everything), **PATCH** (change only some fields), **DELETE**,
plus a better list: **search** (`?q=`), **sorting** (`?sort_by=price&order=desc`) and the **X-Total-Count** header.

## What's new
```
25-crud-part2/
├── app/
│   ├── models/course.py        # + updated_at  (onupdate=func.now())
│   ├── models/teacher.py       # + email (unique)            - homework answer (Video 24)
│   ├── schemas/course.py       # + CourseUpdate (every field optional, null not allowed)
│   ├── services/course_service.py   # update_course, search, sorting, count_matching, get_course_by_title
│   ├── dependencies.py         # + Sorting (Literal whitelist), q in CourseFilter, TeacherDep
│   ├── routers/courses.py      # PUT · PATCH · GET /courses/by-title/{title} · X-Total-Count
│   └── main.py                 # CORS: + PATCH, expose X-Total-Count
└── tests/test_crud2.py
```

## Run it
```bash
cd 25-crud-part2
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env  - then set API_KEY
del coursehub.db                # new columns again (updated_at, teachers.email) - Alembic comes later
fastapi dev app/main.py
pytest -v                       # 82 passed
```

## PUT vs PATCH
```python
@router.put("/{course_id}", response_model=CourseOut)            # the FULL course - every field required
def replace_course(course: CourseDep, data: CourseCreate, db: DBSession) -> Course:
    return course_service.update_course(db, course, data.model_dump())

@router.patch("/{course_id}", response_model=CourseOut)          # only the fields the client sent
def update_course(course: CourseDep, data: CourseUpdate, db: DBSession) -> Course:
    return course_service.update_course(db, course, data.model_dump(exclude_unset=True))

# the service
for field, value in changes.items():
    setattr(course, field, value)       # -> UPDATE courses SET price=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
```
| | `exclude_unset=True` | `exclude_none=True` |
|---|---|---|
| leaves out | fields the client did **not send** | fields whose value **is None** |
| use for PATCH | ✅ | ❌ (can't tell "not sent" from "sent null") |

## Search & sorting
```python
query.where(Course.title.icontains(q, autoescape=True))     # lower(title) LIKE '%' || lower(?) || '%'
SortField = Literal["id", "title", "price", "created_at"]   # anything else -> 422
column = SORT_COLUMNS[sort_by]
query.order_by(column.desc() if order == "desc" else column.asc(), Course.id)
```
`GET /courses?q=docker&sort_by=price&order=desc&limit=2` → 2 courses + header `X-Total-Count: 5`.

## Interview questions
1. **PUT vs PATCH?** PUT replaces the whole resource – the client sends every field. PATCH changes only the fields that are sent. In FastAPI: PUT uses the full schema, PATCH an all-optional schema with `model_dump(exclude_unset=True)`.
2. **How do you let users sort by a column safely?** Never build SQL from user text. Restrict `sort_by` to a whitelist (`Literal` → 422 for anything else), map it to a real column, and add a unique tie-breaker (the id) so pages are stable.
3. **What status code for a successful DELETE?** Usually **204 No Content** – success with no body. Deleting again returns 404; the end state is the same, so DELETE is idempotent.

## Homework
1. `PATCH /students/{student_id}` with a `StudentUpdate` schema – a duplicate email → **409** "Email already registered".
2. `DELETE /students/{student_id}` – admins only, **204**.
3. `GET /students?q=...&sort_by=name|email|created_at&order=asc|desc` + the `X-Total-Count` header.
4. Tests for each.

Answer at the start of Video 26.
