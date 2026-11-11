# 43 – OAuth2 Scopes

**Video 43** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, users + courses, roles from Video 42): **scopes** – the
client asks for them at login, the server grants at most what the **role** allows, the token
carries them in the `scope` claim, and every endpoint names the scope it needs with
**`Security(...)`**. `SecurityScopes` tells the dependency what this request needs.

## Run it
```bash
cd 43-oauth2-scopes
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.login          # who asks for what - and what the token really gets
python -m demos.matrix         # 5 tokens x 4 endpoints + the WWW-Authenticate header
python -m demos.downgrade      # the token says courses:write - the role says no
python -m demos.stacking       # how SecurityScopes collects scopes (and caches)
fastapi dev app/main.py        # /docs -> Authorize -> tick the scopes you want
python -m app.make_admin you@example.com
pytest                         # 15 passed (SQLite and PostgreSQL)
```

## Project
```
app/
  roles.py           Role · SCOPES (name -> description) · ROLE_SCOPES · grant_scopes()
  security.py        create_access_token(user_id, scopes) -> claim "scope": "a b c"
  deps.py            OAuth2PasswordBearer(scopes=SCOPES) · get_current_user(SecurityScopes, ...)
                     Me · CourseReader · CourseWriter = Annotated[User, Security(...)]
  routers/auth.py    POST /users · POST /token (form.scopes) · GET /me
  routers/courses.py GET (courses:read) · POST (courses:write)
  routers/admin.py   APIRouter(dependencies=[Security(get_current_user, scopes=["users:manage"])])
demos/   login · matrix · downgrade · stacking
tests/   test_login · test_scopes
```

## Roles vs scopes
| | Role (Video 42) | Scope (today) |
|---|---|---|
| belongs to | the **user** | the **token** |
| answers | what may this person do? | what may this token do? |
| chosen by | an admin | the client, at login (`scope=...`) |
| lives | in the database | in the JWT (`"scope": "me courses:read"`) |

The server grants `requested ∩ ROLE_SCOPES[role]` (nothing requested → everything the role
allows). Every request checks **both**: the scope must be in the token **and** still allowed by
the user's role – a demoted teacher's old token stops working at once.

| Token | GET /me | GET /courses | POST /courses | GET /admin/users |
|---|---|---|---|---|
| Meera, student (all) | 200 | 200 | 403 | 403 |
| Ravi, teacher (all) | 200 | 200 | 201 | 403 |
| Ravi (`courses:read`) | 403 | 200 | 403 | 403 |
| Asha, admin (all) | 200 | 200 | 201 | 200 |
| Asha (`courses:read`) | 403 | 200 | 403 | 403 |

## Rules
- Scopes in the request and in the token are **one string, separated by spaces** (RFC 6749, 3.3).
- The answer of `/token` includes `scope` – the client must see when it got **less** than it asked for (RFC 6749, 5.1).
- An unknown scope is a **400**; a scope the role doesn't allow is simply left out.
- A missing scope is a **403** with `WWW-Authenticate: Bearer error="insufficient_scope", scope="..."` (RFC 6750, 3.1). FastAPI's own tutorial uses 401 – both work, 403 matches the RFC: the token is valid, it's just not enough.
- `SecurityScopes` collects the scopes of the **whole chain** (`Security` inside `Security`); a dependency with the **same** scopes runs once per request, with **different** scopes once per set.

## Interview questions
1. **What are OAuth2 scopes?** Permissions attached to a token, not to a user. The client asks for scopes at login, the server grants a subset, and each endpoint checks that the token has the scope it needs – so a reporting script can get a read-only token from an admin account.
2. **How do you use scopes in FastAPI?** Declare them in `OAuth2PasswordBearer(scopes={...})`, require them with `Security(dependency, scopes=[...])`, and read them in the dependency with a `SecurityScopes` parameter (`.scopes`, `.scope_str`). At login, `OAuth2PasswordRequestForm.scopes` has what the client asked for.
3. **Roles or scopes?** Both: the role limits what a **user** may ever get, the scopes limit what one **token** may do. Grant `requested ∩ role`, and check both on every request.

## Homework
1. A new scope `courses:delete` (admins only) and `DELETE /courses/{course_id}` that needs it.
2. `GET /me/token` – the scopes of the token you're using right now, and when it expires (hint: a dependency that returns the decoded claims).
3. Tests for both.

Answer at the start of Video 44 (Email Verification and Password Reset).
