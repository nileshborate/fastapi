# 44 – Email Verification and Password Reset

**Video 44** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, users + link_tokens): **email verification** after
registering and a **password reset** – with links that are **random, hashed, expiring and one-time**,
answers that **don't reveal which emails exist**, a swappable **mailer**, and emails sent with
FastAPI's **BackgroundTasks** after the answer.

## Run it
```bash
cd 44-email-verification
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.signup         # register -> email -> 403 -> verify -> 200 -> the link again: 400
python -m demos.forgot         # known vs unknown email: the same 202 · reset once · expired
python -m demos.storage        # the token in the email vs its SHA-256 in the database
python -m demos.background     # BackgroundTasks: the answer first, the email after it
fastapi dev app/main.py        # /docs - the emails are printed in the terminal
pytest                         # 10 passed (SQLite and PostgreSQL)
```

## Project
```
app/
  config.py          FRONTEND_URL · VERIFY_LINK_HOURS=24 · RESET_LINK_MINUTES=30
  models.py          User.is_verified · LinkToken (purpose, token_hash, expires_at, used_at)
  links.py           hash_token · issue_link (old links die) · use_link (once, not expired)
  mailer.py          Email · Mailer (Protocol) · ConsoleMailer · get_mailer()
  emails.py          verify_email · reset_email - the link carries the token
  routers/auth.py    POST /users · /verify-email · /verify-email/resend · /token
                     POST /password/forgot · /password/reset · GET /me
demos/   signup · forgot · storage · background
tests/   test_verify · test_reset   (a FakeMailer via dependency_overrides)
```

## The flows
```
register        POST /users                -> 201 + email "Confirm your email" (link, 24 h)
log in          POST /token                -> 403 "Please verify your email first"
verify          POST /verify-email {token} -> 200 is_verified: true   (again: 400)
forgot          POST /password/forgot      -> 202 "If the email belongs to an account ..."
reset           POST /password/reset       -> 200 (link, 30 min, once) - old password: 401
```

## Rules
- **The token is random** (`secrets.token_urlsafe(32)` – 256 bits), **not** a JWT: a link must work **once**, so the server needs a row anyway.
- **Store only the SHA-256** of the token – a stolen database copy holds no working links.
- **Every bad link gets the same 400** "Invalid or expired link": unknown, used, expired or the wrong purpose.
- **Only the newest link works** – a new link kills the older unused ones of the same purpose.
- **Forgot password answers the same 202** for every email – nobody learns who has an account.
- **Short lives:** verify 24 hours, reset 30 minutes. A reset link also proves the inbox → `is_verified = True`.
- Send emails with **BackgroundTasks** – the answer doesn't wait for the mail server.
- Next video: **rate limiting**, so nobody can request a thousand reset emails.

## Interview questions
1. **How do you build a safe password reset?** A random, single-use, short-lived token: generate it with `secrets`, store only its hash with an expiry, email the link, and on use check hash + purpose + not used + not expired in one query, then mark it used. Answer "forgot password" the same for every email.
2. **Why not a JWT for the reset link?** A JWT is valid until it expires and can't be "used up" – a leaked link would work many times. One-time use needs server state, so a random token plus a database row is simpler and safer.
3. **What are BackgroundTasks in FastAPI?** Functions you add with `tasks.add_task(...)` that run after the response is sent – good for short side jobs like sending an email. For long or important jobs that must survive a restart, use a real task queue.

## Homework
1. Change the password when you're logged in: `POST /me/password` `{"old_password", "new_password"}` – and kill all open reset links of that user.
2. Send a "your password was changed" email after every reset and change (BackgroundTasks).
3. Tests for both.

Answer at the start of Video 45 (API Security Hardening).
