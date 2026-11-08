# 37 – User Registration and Password Hashing

**Video 37** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, the layers from Video 35): a real **users table**,
**Argon2** password hashes with **pwdlib**, and a **unique email**.

## Run it
```bash
cd 37-user-registration
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.argon2_demo      # the hash string · time · bcrypt -> Argon2 upgrade · 72 bytes
fastapi dev app/main.py          # http://127.0.0.1:8000/docs
pytest                           # 15 passed (SQLite and PostgreSQL)
```

## Project
```
app/
  models/user.py        users: email (UNIQUE index) · full_name · password_hash · is_active · created_at
  security.py           NEW: pwdlib PasswordHash((Argon2Hasher(), BcryptHasher())) · DUMMY_HASH
  schemas.py            UserCreate (EmailStr, lower case, password rules) · UserOut (NO hash)
  repositories/users.py get · get_by_email · add
  uow.py                one session · commit: IntegrityError -> "Email already registered"
  services/users.py     register · get · authenticate (one message · dummy hash · upgrade)
  routers/users.py      POST /users (201) · GET /users/{id} · POST /auth/check (a preview)
  errors.py · main.py   DomainError -> HTTP (401 with WWW-Authenticate)
demos/argon2_demo.py
tests/   test_register · test_auth · test_security
```

## The Argon2 hash string
```
$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>
 algorithm  version  memory 64 MB, 3 passes, 4 lanes
```
Everything needed to check the password later is inside – the salt too. Nothing else to store.

## Rules
- **Never** store or log a password – only the hash. `UserOut` has no hash field.
- **Argon2id** for new hashes (the winner of the Password Hashing Competition). bcrypt only to **read** old hashes – it also stops at **72 bytes**.
- `verify_and_update` → an old hash is **upgraded** at the next successful login.
- **Unique email**: lower case it, check it in the service – the **UNIQUE index** is the last safety net (two sign-ups at the same moment → `IntegrityError` → 409).
- **One message** for "no such email" and "wrong password" – and the same work (a dummy hash), so the time doesn't tell either.
- Password rules: 8–128 characters, not a common password, not the email name.

## Interview questions
1. **How do you store passwords?** Never the password – a slow, salted hash, today Argon2id (or bcrypt). The salt and the cost are inside the hash string. On login: hash the typed password with the same salt and compare.
2. **Why Argon2 and not bcrypt or SHA-256?** SHA-256 is fast – billions of guesses per second on a GPU. bcrypt is slow but uses little memory and stops at 72 bytes. Argon2id is slow AND needs a lot of memory, which makes GPU attacks expensive.
3. **How do you make the email unique?** Normalize it (lower case), check it in the service for a nice 409, and put a UNIQUE index on the column – only the database can stop two requests at the same moment.

## Homework
1. `PATCH /users/{user_id}/password` `{"old_password", "new_password"}` – check the old one (401), the same password rules as registration (422), store the new **hash**.
2. `GET /users?email=asha@...` – find a user by email, case-insensitive, 404 if unknown.
3. Tests for both – check that the stored hash changed and still starts with `$argon2id$`.

Answer at the start of Video 38 (JWT Explained).
