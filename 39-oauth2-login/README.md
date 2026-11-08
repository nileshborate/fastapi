# 39 – Login with the OAuth2 Password Flow

**Video 39** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, a users table with Argon2 hashes): a real login with the
**OAuth2 password flow** – `POST /token` with a **form**, `OAuth2PasswordBearer`, and the
**Authorize** button in Swagger.

## Run it
```bash
cd 39-oauth2-login
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.login_form     # the form body · JSON is refused · the OpenAPI security scheme
fastapi dev app/main.py        # /docs -> POST /users (register) -> Authorize -> GET /users/me
pytest                         # 9 passed (SQLite and PostgreSQL)
```

## Project
```
app/
  config.py         DATABASE_URL · JWT_SECRET (min 32) · ACCESS_TOKEN_MINUTES
  security.py       hash_password / verify_password (Argon2) · create / decode_access_token (JWT)
  models.py         users
  schemas.py        UserCreate · UserOut · Token {access_token, token_type}
  routers/auth.py   POST /token  - OAuth2PasswordRequestForm
  routers/users.py  POST /users · GET /users/me - OAuth2PasswordBearer(tokenUrl="token")
demos/login_form.py
tests/   test_login · test_me
```

## The flow
```
client                                   API
  | POST /token                            |
  |  Content-Type: application/x-www-form-urlencoded
  |  username=asha%40example.com&password=...
  |--------------------------------------->|  check the Argon2 hash
  |<---------------------------------------|  {"access_token": "eyJ...", "token_type": "bearer"}
  | GET /users/me                          |
  |  Authorization: Bearer eyJ...          |
  |--------------------------------------->|  OAuth2PasswordBearer -> the token -> decode -> user
```

## Rules
- The password flow sends a **form**, not JSON – `python-multipart` (in `fastapi[standard]`) reads it.
- The field is called `username` – our users type their **email** there.
- The answer must be `{"access_token": ..., "token_type": "bearer"}` – Swagger (and other OAuth2 clients) read exactly that.
- `OAuth2PasswordBearer(tokenUrl="token")`: reads the header, answers **401 Not authenticated** if it's missing, and adds the security scheme to OpenAPI → the **Authorize** button.
- `tokenUrl` is relative: `"token"` → `/token`.

## Interview questions
1. **What is the OAuth2 password flow, and when do you use it?** The client sends the user's username and password to the token endpoint and gets an access token back. Use it for your own first-party apps (your frontend, your mobile app) – never let a third-party app collect your users' passwords.
2. **What does `OAuth2PasswordBearer` do?** It's a dependency that reads `Authorization: Bearer <token>` and returns the token string – 401 if it's missing. It does **not** check the token. And it tells OpenAPI where the token endpoint is, so Swagger shows the Authorize button.
3. **Why a form and not JSON for `/token`?** The OAuth2 spec defines the token request as `application/x-www-form-urlencoded` with `grant_type`, `username`, `password` – standard clients (Swagger, Postman, libraries) send exactly that.

## Homework
1. `POST /token`: block inactive users (`is_active=False`) – the same 401 message as a wrong password.
2. Make the access token lifetime visible: add `"expires_in"` (seconds) to the `/token` answer.
3. Tests: an inactive user can't log in; `expires_in` is 900 with the default settings.

Answer at the start of Video 40 (Protected Routes and the Current User).
