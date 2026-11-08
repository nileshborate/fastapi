# 40 – Protected Routes and the Current User

**Video 40** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, users + courses): one `get_current_user` dependency that
protects every route, **401 vs 403**, an **owner check**, optional login, a router protected as a
whole, and tests with `dependency_overrides`.

## Run it
```bash
cd 40-protected-routes
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.chain          # the order of a dependency chain - get_db runs only ONCE
python -m demos.tokens         # 7 tokens against GET /me: 401 · 401 · ... · 403 · 200
fastapi dev app/main.py        # /docs -> POST /users -> Authorize -> POST /courses
pytest                         # 18 passed (SQLite and PostgreSQL) - 15 + 3 homework
```

## Project
```
app/
  deps.py            NEW: oauth2_scheme · get_current_user · get_current_active_user
                          get_optional_user · CurrentUser · OptionalUser
  models.py          User 1-N Course (owner_id)
  security.py        Argon2 + JWT (create_access_token(minutes=...) for the demo)
  routers/auth.py    POST /users · POST /token
  routers/courses.py GET (public) · POST (login) · PATCH/DELETE (owner only -> 403)
  routers/me.py      APIRouter(dependencies=[Depends(get_current_active_user)])
demos/   chain.py · tokens.py
tests/   test_current_user · test_courses · test_overrides · test_chain
```

## The chain
```
GET /me
  oauth2_scheme            reads "Authorization: Bearer ..."      no header        -> 401 Not authenticated
  get_current_user         decode (signature, exp) -> sub -> user  anything wrong   -> 401 Could not validate
  get_current_active_user  user.is_active?                         inactive         -> 403 Inactive user
  the endpoint             gets a User object - nothing to check any more
```
FastAPI runs every dependency **once per request** and reuses the result (here: `get_db`).

## 401 vs 403 vs 404
| Status | Question | Example |
|---|---|---|
| 401 | Who are you? – no or a bad token | no header · expired · other secret · deleted user |
| 403 | We know you – but no | inactive user · not the owner of the course |
| 404 | It doesn't exist | `PATCH /courses/99` |

## Four ways to protect
| Way | Code | Use |
|---|---|---|
| a parameter | `user: CurrentUser` | you need the user in the function |
| optional | `user: OptionalUser` (`auto_error=False`) | public, but personal with a token |
| the decorator | `@router.get(..., dependencies=[Depends(...)])` | only the check, no value |
| the router | `APIRouter(dependencies=[Depends(...)])` | every route in the router |

## Interview questions
1. **How do you protect a route in FastAPI?** With a dependency: `get_current_user` reads the token (`OAuth2PasswordBearer`), validates it, loads the user and raises 401 if anything is wrong. Every protected endpoint declares it – as a parameter, in `dependencies=[...]`, or on the whole router.
2. **When 401 and when 403?** 401: the server doesn't know who you are (no token, invalid or expired token). 403: it knows you, but you're not allowed (wrong role, inactive, not the owner). Logging in again helps with 401, never with 403.
3. **How do you test protected endpoints?** Either log in for real in the test and send the Bearer header, or replace the dependency: `app.dependency_overrides[get_current_active_user] = lambda: fake_user` – and clear the overrides afterwards.

## Homework
1. `GET /me/courses/{course_id}` – only YOUR course; someone else's course answers **404**, not 403. Write in a comment why (hint: what does 403 tell an attacker?).
2. `PATCH /me` `{"full_name": ...}` – change your own name (the router already protects it).
3. Tests – one of them with `dependency_overrides`.

Answer at the start of Video 41 (Refresh Tokens and Logout).

## Homework answer (shown at the start of Video 41)
```python
# routers/me.py - only YOUR course; somebody else's is a 404, not a 403
@router.get("/courses/{course_id}", response_model=CourseOut)
async def my_course(course_id: int, user: CurrentUser, db: DB) -> Course:
    # 403 would tell an attacker "course 7 exists, it's just not yours"
    stmt = select(Course).where(Course.id == course_id, Course.owner_id == user.id)
    course = await db.scalar(stmt)
    if course is None:
        raise HTTPException(404, "Course not found")
    return course

@router.patch("", response_model=UserOut)          # PATCH /me {"full_name": ...}
async def update_me(data: MeUpdate, user: CurrentUser, db: DB) -> User:
    user.full_name = data.full_name                 # the user comes from the token
    await db.commit()
    ...
```
The owner check is part of the `WHERE` – one query, and "not yours" looks exactly like "doesn't
exist". `tests/test_homework40.py` – 3 tests, one with `dependency_overrides`.
`pytest` → **18 passed** (SQLite and PostgreSQL).
