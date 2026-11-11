# 42 – Role-Based Access Control

**Video 42** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, users + courses + enrollments): three **roles** –
admin, teacher, student – a **dependency factory** `require_roles(...)`, a **permission map**
with `require_permission(...)`, the **owner rule** on top of a role, an `/admin` router, and a
script for the very first admin.

## Run it
```bash
cd 42-role-based-access
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.matrix                     # 8 requests x guest / student / teacher / admin
python -m demos.promote                    # the SAME token - a new role works at once
python -m demos.factory                    # require_roles(...) builds a new function each time
fastapi dev app/main.py                    # /docs - register, then:
python -m app.make_admin you@example.com   # the first admin: a script, never the API
pytest                                     # 20 passed (SQLite and PostgreSQL) - 17 + 3 homework
```

## Project
```
app/
  roles.py           Role (StrEnum) · PERMISSIONS: role -> set of permissions · has_permission
  models.py          User.role (CHECK constraint) · Course.teacher_id · Enrollment (unique)
  deps.py            get_current_user · CurrentUser · require_roles(*roles) · require_permission(p)
  make_admin.py      python -m app.make_admin <email>
  routers/auth.py    POST /users (always a student) · POST /token · GET /me
  routers/courses.py GET (public) · POST · PATCH (owner or admin) · DELETE · POST /enroll
  routers/admin.py   APIRouter(dependencies=[Depends(require_roles(Role.ADMIN))])
demos/   matrix · promote · factory
tests/   test_matrix (8 x 4) · test_roles · test_overrides
```

## Who may do what
| Request | guest | student | teacher | admin |
|---|---|---|---|---|
| `GET /courses` | 200 | 200 | 200 | 200 |
| `POST /courses` | 401 | 403 | 201 | 201 |
| `PATCH /courses/{id}` – own course | 401 | 403 | 200 | 200 |
| `PATCH /courses/{id}` – somebody else's | 401 | 403 | **403** | 200 |
| `POST /courses/{id}/enroll` | 401 | 201 | 403 | 403 |
| `GET /admin/users` | 401 | 403 | 403 | 200 |
| `PATCH /admin/users/{id}/role` | 401 | 403 | 403 | 200 |
| `DELETE /courses/{id}` | 401 | 403 | 403 | 204 |

## Rules
- **Nobody picks their own role.** `UserCreate` has `extra="forbid"` – `{"role": "admin"}` is a 422; every new user is a student.
- **The role comes from the database**, not from the token – a role change works at once, with the same token.
- **The first admin** comes from a script on the server (`python -m app.make_admin`), never from the API.
- An admin can't change their **own** role – the last admin could lock everybody out.
- The database guards the roles too: `CHECK (role IN ('admin', 'teacher', 'student'))`.
- **A role is not always enough:** a teacher may update courses – but only their **own** (the owner rule), unless they are an admin.

## Interview questions
1. **What is RBAC?** Role-based access control: users get roles, and roles get permissions. Endpoints check a permission (or a role), never a single user – so adding a new teacher is one row, not a code change.
2. **How do you build a role check in FastAPI?** A dependency factory: `require_roles(*roles)` returns a new async function that depends on the current user and raises 403 if the role doesn't match. Use it as a parameter, in `dependencies=[...]`, or on a whole router.
3. **Should the role be inside the JWT?** It can be (fewer database reads), but then a role change only works after the token expires, and the token must never be trusted beyond its signature. Loading the user from the database on each request – as we already do – makes role changes immediate.

## Homework
1. `GET /courses/{course_id}/students` – the enrolled students of a course: only the course's teacher or an admin (others: 403).
2. `PATCH /admin/users/{user_id}/active` `{"is_active": false}` – admins block users; an admin can't block themselves.
3. Tests for both.

Answer at the start of Video 43 (OAuth2 Scopes).

## Homework answer (shown at the start of Video 43)
```python
# routers/courses.py - the students of a course: its OWN teacher or an admin
@router.get("/{course_id}/students", response_model=list[UserOut])
async def course_students(course_id: int, user: CurrentUser, db: DB) -> list[User]:
    course = await get_course(db, course_id)                    # 404 first
    if user.role != Role.ADMIN and course.teacher_id != user.id:
        raise HTTPException(403, "Only the course's teacher or an admin can see this")
    stmt = (select(User).join(Enrollment, Enrollment.user_id == User.id)
            .where(Enrollment.course_id == course_id).order_by(User.id))
    return list(await db.scalars(stmt))

# routers/admin.py - the router already checks "admin"; you can't block yourself
@router.patch("/users/{user_id}/active", response_model=UserOut)
async def set_active(user_id: int, data: ActiveUpdate, admin: CurrentUser, db: DB) -> User:
    if user_id == admin.id:
        raise HTTPException(400, "You can't block yourself")
    ...                                   # 404 · user.is_active = data.is_active · commit
```
A blocked user's old token gets **403 Inactive user**, a new login **401**.
`tests/test_homework42.py` – 3 tests. `pytest` → **20 passed** (SQLite and PostgreSQL).
