# 41 – Refresh Tokens and Logout

**Video 41** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, users + refresh_tokens): a **short access token** (15 minutes)
and a **long refresh token** (7 days), **rotation** on every refresh, **reuse detection**, logout of
one device, and **"log out everywhere"** that kills even the access tokens.

## Run it
```bash
cd 41-refresh-tokens
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.anatomy        # the two tokens: type, jti, ver, 15 minutes vs 7 days
python -m demos.client_flow    # access token expired -> 401 -> refresh -> 200
python -m demos.rotation       # refresh twice, a thief replays token 1 -> everybody out
python -m demos.logout         # logout: the refresh token dies, the access token NOT (yet)
fastapi dev app/main.py        # /docs
pytest                         # 16 passed (SQLite and PostgreSQL) - 12 + 4 homework
```

## Project
```
app/
  config.py          ACCESS_TOKEN_MINUTES=15 · REFRESH_TOKEN_DAYS=7
  models.py          User (+ token_version) · RefreshToken (jti, expires_at, revoked_at, replaced_by)
  security.py        create_access_token (type, ver) · create_refresh_token (type, jti) · decode_token
  tokens.py          issue_pair · rotate (reuse detection) · revoke_all
  deps.py            get_current_user: type must be "access", ver must match
  routers/auth.py    POST /users · /token · /token/refresh · /logout · /logout/all
  routers/me.py      GET /me · GET /me/sessions
demos/   anatomy · client_flow · rotation · logout
tests/   test_login · test_refresh · test_logout
```

## The two tokens
| | Access token | Refresh token |
|---|---|---|
| lives | 15 minutes | 7 days |
| sent | with **every** request (`Authorization: Bearer`) | **only** to `POST /token/refresh` |
| checked | signature + exp + `type="access"` + `ver` | signature + exp + `type="refresh"` + a row in the table |
| stored on the server | nothing | a row: `jti`, `expires_at`, `revoked_at`, `replaced_by` |
| stolen? | works until it expires (≤ 15 minutes) | rotation + reuse detection |

## Rotation and reuse detection
```
login         -> token 1
refresh(1)    -> token 2      row 1: revoked, replaced_by = 2
refresh(2)    -> token 3      row 2: revoked, replaced_by = 3
refresh(1)    -> 401 "Refresh token reuse detected"  -> revoke ALL of the user's tokens
```
Token 1 was already used, so **two** people have it – we can't tell which one is the thief, so
everybody logs in again.

## Logout
| Endpoint | Kills | Access tokens |
|---|---|---|
| `POST /logout` `{"refresh_token": ...}` | this device's refresh token | still work until they expire |
| `POST /logout/all` (Bearer) | every refresh token | dead at once: `token_version + 1`, the old `ver` doesn't match |

Logout always answers **204** – logging out never fails.

## Interview questions
1. **Why two tokens instead of one long access token?** The access token goes with every request, so it leaks most easily – a short life limits the damage. The refresh token travels rarely (only to one endpoint), so it can live long, and because the server keeps a row for it, it can be revoked.
2. **What is refresh token rotation, and what is reuse detection?** Every refresh returns a NEW refresh token and kills the old one. If an old, already-used token shows up again, two parties have it – the server revokes the whole family and the user must log in again.
3. **How do you log out a JWT the server doesn't store?** You can't "delete" it – it's valid until `exp`. So: keep access tokens short, revoke the refresh token on logout, and for an immediate logout check something in the database – a `token_version` (as here) or a denylist of `jti`s.

## Homework
1. `GET /me/sessions` already lists the alive refresh tokens – add `DELETE /me/sessions/{id}`: log out ONE other device (only your own sessions – somebody else's is a 404).
2. Changing the password must log out everywhere: `PATCH /me/password` `{"old_password", "new_password"}` – check the old one, save the new hash, revoke all refresh tokens, `token_version + 1`.
3. Tests for both.

Answer at the start of Video 42 (Role-Based Access Control).

## Homework answer (shown at the start of Video 42)
```python
# routers/me.py - log out ONE device; somebody else's session is a 404
@router.delete("/sessions/{session_id}", status_code=204)
async def end_session(session_id: int, user: CurrentUser, db: DB) -> Response:
    stmt = select(RefreshToken).where(RefreshToken.id == session_id,
                                      RefreshToken.user_id == user.id,
                                      RefreshToken.revoked_at.is_(None))
    ...                                  # None -> 404, else revoked_at = now

# a new password logs out EVERYWHERE - but this device gets a fresh pair
@router.patch("/password", response_model=TokenPair)
async def change_password(data: PasswordChange, user: CurrentUser, db: DB) -> TokenPair:
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Old password is wrong")
    user.password_hash = hash_password(data.new_password)
    await revoke_all(db, user.id)        # every refresh token dies
    user.token_version += 1              # every access token dies
    pair, _ = await issue_pair(db, user) # ...but THIS device stays logged in
    await db.commit()
    return pair
```
`tests/test_homework41.py` – 4 tests. `pytest` → **16 passed** (SQLite and PostgreSQL).
