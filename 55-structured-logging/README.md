# 55 – Structured Logging: JSON lines, a request id on every line, errors with context

**Video 55** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project. Plain text logs are fine on a laptop, but in production three requests run at
the same time and their lines get mixed. Here every log line is **one JSON object** with an **event
name**, **fields**, and the **request id** – added automatically with a `ContextVar`, a logging
`Filter` and a middleware. Then you can **find one request** among thousands and **answer
questions** from your logs. Only the standard library – no extra package.

## Run it
```bash
cd 55-structured-logging
pip install -r requirements.txt
fastapi dev app/main.py                  # JSON lines in the terminal
LOG_JSON=false fastapi dev app/main.py   # plain text (Windows PowerShell: $env:LOG_JSON="false")

python -m demos.plain        # 3 requests at once, plain text: 18 lines - whose is whose?
python -m demos.json_logs    # the same as JSON: find one request · count by status · the slowest
python -m demos.errors       # a 500 with request_id "support-42" + traceback · events · card "***"
pytest                       # 10 passed
```

## Project
```
app/
  config.py          service · log_level (INFO) · log_json (True)        - from env vars
  logging_setup.py   request_id_var (ContextVar) · RequestIdFilter · JsonFormatter · setup_logging()
  middleware.py      RequestContextMiddleware: X-Request-ID in/out · request.done · request.failed
  services.py        enroll() + build_report() - log EVENTS with fields: log.info("x", extra={...})
  main.py            setup_logging() · POST /enrollments · GET /reports/{id} · GET /boom (a real bug)
demos/   common · plain · json_logs · errors        tests/   conftest (logs fixture) · test_logging · test_homework55
```

## One line
```json
{"ts": "2026-11-12T10:03:14.398+00:00", "level": "INFO", "logger": "app.http", "event": "request.done",
 "request_id": "e532c314977c", "service": "course-hub", "method": "GET", "path": "/reports/1",
 "status": 200, "duration_ms": 304.5}
```

## How it works
| piece | job |
|---|---|
| `ContextVar("request_id", default="-")` | one value **per request**, even with many requests at once (async + threads) |
| `RequestContextMiddleware` | reuse `X-Request-ID` or make one (`uuid4().hex[:12]`), `set` → `reset`, return it in the response |
| `RequestIdFilter` (on the handler) | copies the id onto **every** record – your code never passes it |
| `JsonFormatter` | `ts` (UTC) · `level` · `logger` · `event` · `request_id` · `service` + every `extra=` field · `exc_type` + `traceback` |
| `SECRET_KEYS` | `password`, `card_number`, `token`, `authorization` → `"***"` |
| `dictConfig` | root level from `LOG_LEVEL`, uvicorn's loggers through **our** handler, `httpx`/`httpcore` only WARNING |

## Rules
- Log **events with fields** (`log.info("enrollment.created", extra={"course_id": 2})`), not sentences with values glued in.
- **One JSON object per line**, to stdout – the platform (Docker, Kubernetes, CloudWatch, Loki, ELK) collects it.
- A **request id** on every line; accept it from the caller, return it in `X-Request-ID` and in error bodies.
- Levels: DEBUG details · INFO events · WARNING something odd · ERROR it failed. Production = INFO.
- `log.exception(...)` inside `except` → level ERROR **and** the traceback.
- Never log secrets or whole request bodies; redact by key.

## Interview questions
1. **What is structured logging and why use it?** Every log entry is data – usually one JSON object per line with fixed fields (time, level, event, request id) plus event-specific fields. Machines can filter, count and alert on it; plain text needs fragile regexes.
2. **How do you trace one request through the logs?** Give each request a correlation id: reuse the caller's `X-Request-ID` or generate one, store it in a `ContextVar` in a middleware, add it to every record with a logging filter, and return it to the client so support can search for it.
3. **What should you never log?** Passwords, tokens, API keys, card numbers, full personal data and whole request bodies. Redact sensitive keys in the formatter, and keep DEBUG off in production.

## Homework
1. **A slow-request warning:** a new setting `slow_ms` (default 500); when a request takes longer, also log **WARNING** `request.slow` with `path` and `duration_ms`.
2. **More context:** add `client_ip` and `user_agent` to every `request.done` line.
3. Tests for both.

Answer at the start of Video 56 (Health Checks and Metrics).

## Homework answer (shown at the start of Video 56)
**1. A slow-request warning.** `config.py` gets `slow_ms: float = 500` (so `SLOW_MS=250` works too).
In the middleware's `finally`, after `request.done`:
```python
if duration_ms > get_settings().slow_ms:
    log.warning("request.slow", extra={"path": request.url.path, "duration_ms": duration_ms})
```
A separate WARNING line (not just a field) – so you can alert on it, and it shows up when you filter by level.

**2. More context.** `request.done` gets `client_ip` (`request.client.host`) and `user_agent`
(`request.headers.get("user-agent")`). Behind a load balancer `request.client.host` is the proxy's address –
run `uvicorn --proxy-headers --forwarded-allow-ips=<proxy ip>` so it reads `X-Forwarded-For`.

Real run with `SLOW_MS=250`:
```
{'level': 'INFO', 'event': 'request.done', 'path': '/reports/2', 'status': 200, 'duration_ms': 303.5, 'client_ip': '127.0.0.1', 'user_agent': 'course-app/3.1'}
{'level': 'WARNING', 'event': 'request.slow', 'path': '/reports/2', 'duration_ms': 303.5}
{'level': 'INFO', 'event': 'request.done', 'path': '/enrollments', 'status': 201, 'duration_ms': 2.6, 'client_ip': '127.0.0.1', 'user_agent': 'python-httpx/0.28.1'}
```

**3. Tests:** `tests/test_homework55.py` – 3 tests (a slow request is a WARNING with `slow_ms` patched to 100,
a fast one is not, `client_ip` + `user_agent`). `pytest` → **10 passed**.
