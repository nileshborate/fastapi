# 45 – API Security Hardening

**Video 45** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (async, Alembic, users + courses) that is **hard to abuse**: a self-made
**rate limiter** (sliding window, 429 + Retry-After), **input limits** everywhere, a **body size
limit** (413), **security headers**, **TrustedHost**, **CORS**, **HTTPS + HSTS** in production,
**no /docs** in production, and **errors that never leak** – mapped to the **OWASP API Security Top 10 (2023)**.

## Run it
```bash
cd 45-security-hardening
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m demos.brute_force    # 5 tries per minute - then 429, even with the right password
python -m demos.limits         # 1 MB body: 413 · long strings, big numbers, limit=1000000: 422
python -m demos.headers        # development vs production: headers, HSTS, /docs, Host, CORS, 500
fastapi dev app/main.py
pytest                         # 21 passed (SQLite and PostgreSQL) - 18 + 3 homework
```

## Project
```
app/
  config.py          ENVIRONMENT · ALLOWED_HOSTS · CORS_ORIGINS · MAX_BODY_BYTES · LOGIN_LIMIT
  ratelimit.py       RateLimiter (sliding window, fake-able clock) · client_ip()
  middleware.py      BodySizeLimit (Content-Length AND counted bytes) · SecurityHeaders
  schemas.py         max_length / ge / le on every field · extra="forbid"
  deps.py            limit_writes (per user) · limit_ip (per IP and path)
  routers/auth.py    POST /users (per IP) · POST /token (5 / minute / IP + email) · GET /me
  routers/courses.py GET (limit ≤ 100, q ≤ 50) · POST · PATCH (owner only -> 404)
  main.py            create_app(settings): middleware order, docs off in production, safe 500
demos/   brute_force · limits · headers
tests/   test_ratelimit · test_limits · test_hardening
```

## The layers
| Layer | What it stops | Answer |
|---|---|---|
| `SecurityHeaders` (outermost) | the browser misusing our answers | `nosniff` · `DENY` · `no-referrer` · `no-store` · HSTS in production |
| `HTTPSRedirectMiddleware` (production) | passwords and tokens over plain HTTP | 307 → `https://` |
| `TrustedHostMiddleware` | a fake `Host` header (cache poisoning, bad links in emails) | 400 |
| `BodySizeLimit` | a 1 GB body that fills the memory | 413 |
| `CORSMiddleware` | other websites calling us from a user's browser | no CORS headers for unknown origins |
| Pydantic + `Query` limits | huge strings, numbers, pages; fields from outside | 422 |
| `RateLimiter` | password guessing, spam, scraping | 429 + `Retry-After` |
| exception handler | stack traces and secrets in answers | 500 `{"detail", "error_id"}` |

## OWASP API Security Top 10 (2023) – where this course handles it
| Risk | Where |
|---|---|
| API1 Broken Object Level Authorization | owner checks – Videos 40, 42, here: `PATCH /courses/{id}` |
| API2 Broken Authentication | Argon2, JWT, refresh rotation, rate-limited login – Videos 37–41, here |
| API3 Broken Object Property Level Authorization | `extra="forbid"`, response models without secrets |
| API4 Unrestricted Resource Consumption | rate limits, body limit, `limit ≤ 100`, max lengths – here |
| API5 Broken Function Level Authorization | roles and scopes – Videos 42, 43 |
| API6 Unrestricted Access to Sensitive Business Flows | rate limits per user/action, one-time links – Video 44, here |
| API7 Server Side Request Forgery | never fetch user-given URLs without an allow-list |
| API8 Security Misconfiguration | headers, HTTPS, TrustedHost, CORS, no docs, safe errors – here |
| API9 Improper Inventory Management | versioning and docs – later videos |
| API10 Unsafe Consumption of APIs | validate what other APIs send you, like user input |

## Rules
- **Rate-limit before the expensive work** – the login limit runs before Argon2.
- The in-memory limiter is **per process**: with several workers or servers, keep the counters in **Redis**.
- Behind a proxy, `request.client.host` is the proxy: run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy>`.
- Every string gets a `max_length`, every number a range, every list a `limit`.
- **No `/docs` and no `openapi.json` in production** (or put them behind a login).
- **A 500 says nothing** – the details go to the log with an `error_id`.

## Interview questions
1. **How do you rate-limit a FastAPI endpoint?** With a dependency or middleware that counts requests per key (IP, user, IP + email) in a time window and answers **429** with `Retry-After`. In memory for one process; with several workers or servers, in a shared store like Redis.
2. **What is OWASP API4 – Unrestricted Resource Consumption?** An API that lets a client use unlimited CPU, memory, bandwidth or money: no rate limits, unlimited page sizes, huge bodies or strings. Fix it with rate limits, size limits and maximum page sizes.
3. **Which security headers does an API need, and what does HSTS do?** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Cache-Control: no-store` for private data, and **HSTS** (`Strict-Transport-Security`), which tells browsers to use only HTTPS for the domain from now on.

## Homework
1. Rate-limit `POST /users` per email too: at most 3 registrations per hour for the same email domain.
2. Add `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'` to every answer **except** `/docs` (Swagger needs scripts).
3. Tests for both.

Answer at the start of Video 46 (WebSockets Part 1).

## Homework answer (shown at the start of Video 46)
```python
# routers/auth.py - a 4th limiter on app.state: 3 new accounts per hour per email DOMAIN
async def register(data: UserCreate, request: Request, db: DB) -> User:
    domain = data.email.rsplit("@", 1)[1]                 # the email is already lower case
    request.app.state.domain_limiter.check(f"domain:{domain}")   # before Argon2
    ...

# middleware.py - SecurityHeaders: a Content-Security-Policy, but not for Swagger / ReDoc
DOCS_PATHS = ("/docs", "/redoc")
self.csp = (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
extra = list(self.headers)
if not scope["path"].startswith(DOCS_PATHS):
    extra.append(self.csp)
```
`default-src 'none'`: a JSON answer needs no scripts, styles or images – if one is ever shown as a
page, the browser runs nothing. `frame-ancestors 'none'` is the modern `X-Frame-Options: DENY`.
In a real app, limit only unknown or throw-away domains – not gmail.com for everybody.
`tests/test_homework45.py` – 3 tests. `pytest` → **21 passed** (SQLite and PostgreSQL).
