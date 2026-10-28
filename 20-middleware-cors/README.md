# 20 – Middleware and CORS

**FastAPI Mastery: Zero to Production** – Video 20 · Nilesh Technology

Middleware runs for **every** request and response. CORS lets a browser frontend on another origin call your API – safely.

## What's new
```
20-middleware-cors/
├── app/
│   ├── middleware.py   # NEW: request_id_and_timing  (X-Request-ID + X-Process-Time)
│   ├── main.py         # app.middleware("http") · GZipMiddleware · CORSMiddleware
│   └── config.py       # allowed_origins (+ homework: database_url, max_upload_mb, prod validator)
├── frontend/index.html # a tiny frontend on another origin, to see CORS in a real browser
└── tests/test_middleware.py
```

## Run it
```bash
cd 20-middleware-cors
pip install -r requirements.txt
copy .env.example .env                              # Linux/Mac: cp .env.example .env  - then set API_KEY
fastapi dev app/main.py                             # API on http://127.0.0.1:8000
python -m http.server 3000 --directory frontend     # 2nd terminal: frontend on http://localhost:3000
pytest -v                                           # 29 passed
```

## A middleware in 3 steps
```python
async def request_id_and_timing(request: Request, call_next):
    ...                                   # 1. before the endpoint
    response = await call_next(request)   # 2. the rest of the app runs
    response.headers["X-Process-Time"] = ...   # 3. after the endpoint
    return response
```
- Middleware runs for **everything** – also 404s and `/docs`. A dependency runs only for matched endpoints.
- Order: the middleware added **last** is the **outermost** – it runs first on the way in and last on the way out.

## CORS in one table
| Term | Meaning |
|------|---------|
| Origin | scheme + host + port: `http://localhost:3000` ≠ `http://127.0.0.1:8000` |
| Same-origin policy | the **browser** won't let JavaScript read a response from another origin… |
| `Access-Control-Allow-Origin` | …unless the API answers with this header |
| Preflight | an automatic `OPTIONS` request before "non-simple" requests (custom headers like `X-API-Key`, JSON `POST`, `DELETE`) |

CORS is enforced by the **browser**, not the server: the server still runs the request. It is **not** authentication – Postman and curl ignore it.

## Interview questions
1. **What is middleware in FastAPI?** A function (or class) that wraps every request: it runs before the request reaches the routing, calls `call_next(request)`, and can change the response afterwards. Used for logging, timing, request IDs, CORS, compression, security headers. The last one added is the outermost.
2. **What is CORS and why do you need `CORSMiddleware`?** Browsers apply the same-origin policy: JavaScript on one origin can't read responses from another origin unless the server allows it with `Access-Control-Allow-*` headers. `CORSMiddleware` adds those headers and answers preflight `OPTIONS` requests for the origins you list.
3. **Why is `allow_origins=["*"]` with `allow_credentials=True` dangerous?** Starlette then echoes back *any* origin and allows credentials, so any website could make logged-in requests with the user's cookies and read the answers. List the exact frontend origins instead, from settings.

## Homework
1. A middleware that adds security headers to every response: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`.
2. Add `TrustedHostMiddleware` with `allowed_hosts` from settings.
3. A middleware that returns **413** (without calling `call_next`) when `Content-Length` is bigger than `max_upload_mb`.
4. Tests for each.

Answer at the start of Video 21.
