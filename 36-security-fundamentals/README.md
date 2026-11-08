# 36 – Security Fundamentals

**Video 36** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

The start of the security part. Three pairs that people mix up – each one as running code:

| | | |
|---|---|---|
| **Authentication** – *who are you?* | vs | **Authorization** – *what may you do?* |
| **Hashing** – one way (passwords) | vs | **Encryption** – two way, with a key (data) |
| **Sessions** – the server remembers | vs | **Tokens** – signed, the server remembers nothing |

No database today – two users live in `app/users.py`, with **hashed** passwords.

## Run it
```bash
cd 36-security-fundamentals
pip install -r requirements.txt
cp .env.example .env
python -m demos.hashing        # same input = same hash · fast vs slow · salt
python -m demos.encryption     # encrypt + decrypt with a key · the wrong key fails
python -m demos.signing        # a signed token: change it -> "Invalid signature"
fastapi dev app/main.py        # http://127.0.0.1:8000/docs
pytest                         # 13 passed
```
Users: `nilesh` / `admin-pass-123` (admin) · `asha` / `student-pass-123` (student)

## Project
```
app/
  config.py          SECRET_KEY · TOKEN_MINUTES · SESSION_MINUTES · COOKIE_SECURE
  passwords.py       hash_password / verify_password - PBKDF2-SHA256, salt, 600 000 rounds
  tokens.py          create_token / read_token - a tiny HMAC-signed token (JWT: Video 38)
  users.py           two users + authenticate()
  sessions.py        the session store: session id -> username
  deps.py            session_user · token_user (401) · require_admin (403)
  routers/
    session_auth.py  POST /session/login (cookie) · GET /session/me · POST /session/logout
    token_auth.py    POST /token/login · GET /token/me · GET /admin/stats
demos/   hashing.py · encryption.py · signing.py
tests/   test_passwords · test_tokens · test_session_login · test_token_login
```

## 401 vs 403
| Status | Means | Example |
|---|---|---|
| **401 Unauthorized** | we don't know who you are (authentication failed) | no token, wrong token, expired |
| **403 Forbidden** | we know you – but you may not (authorization failed) | a student calls `/admin/stats` |

## Sessions vs tokens
| | Session (cookie) | Token (Bearer) |
|---|---|---|
| The client keeps | a random id (`session_id`) | the signed data itself |
| The server keeps | the list of sessions | nothing – only the secret key |
| Logout | delete the session – **at once** | not possible until it expires (→ Video 41) |
| Good for | browser apps on one domain | mobile apps, APIs, many servers |
| Watch out | CSRF → `SameSite`, `HttpOnly`, `Secure` | keep it short-lived, never put secrets in it |

## Rules to remember
- Never store a password – store a **slow, salted hash** (Argon2 in Video 37).
- Hashing is **not** encryption: a hash can't be turned back.
- A signed token can be **read** by everybody (base64 is not encryption) – but not **changed**.
- Compare secrets with `hmac.compare_digest` (constant time).
- "Wrong username **or** password" – never tell which one was wrong.

## Interview questions
1. **Authentication vs authorization?** Authentication checks *who* you are (login, token) → 401 when it fails. Authorization checks *what* you may do (role, owner) → 403.
2. **Hashing vs encryption – which for passwords?** Hashing: one way, a slow and salted hash. Encryption is two way – whoever gets the key gets every password back.
3. **Sessions vs tokens?** A session id points to data the server keeps – easy to revoke, needs shared storage. A signed token carries the data itself – no server storage, scales easily, but can't be revoked before it expires.

## Homework
1. `POST /token/password` (logged in with a token): `{"old_password", "new_password"}` – check the old one (401), the new one at least 8 characters (422), then store the **new hash**.
2. After **3 wrong passwords** in a row, block that user's login for 60 seconds (429).
3. Tests for both.

Answer at the start of Video 37 (User Registration and Password Hashing).

## Homework answer (shown at the start of Video 37)
```python
# routers/token_auth.py - change the password (logged in with a token)
@router.post("/token/password", status_code=204)
def change_password(data: PasswordChange, user: ... = Depends(token_user)) -> None:
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(401, "Wrong password")
    user.password_hash = hash_password(data.new_password)    # new_password: min_length=8 -> 422

# app/lockout.py + users.check_login - 3 wrong passwords in a row: blocked for 60 s (429)
if lockout.is_blocked(username):          # BLOCKED_UNTIL[username] > now()
    raise HTTPException(429, "Too many wrong passwords - try again later")
```
Both logins (session and token) use `check_login`. A correct password resets the count.
`tests/test_homework36.py` replaces `lockout.now` to jump 61 seconds ahead. `pytest` → **16 passed**.
