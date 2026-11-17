# 56 – Health Checks and Metrics: liveness, readiness, Prometheus /metrics

**Video 56** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project. Logs (Video 55) tell you **what happened to one request**. Health checks tell
the platform **whether to send traffic** to this instance, and metrics tell you **how the whole service
is doing** – requests per second, error rate, latency – as numbers over time.

## Run it
```bash
cd 56-health-metrics
pip install -r requirements.txt          # + prometheus-client · redis
fastapi dev app/main.py                  # /health/live · /health/ready · /metrics

python -m demos.health      # ready · payments slow (timeout 1 s) / 503 = degraded · database gone = 503 · draining
python -m demos.traffic     # 64 real requests -> read /metrics -> rate, error rate, avg + p95 per route
pytest                      # 14 passed
```

## Project
```
app/
  config.py    version 1.4.0 · db_path · payments_url · check_timeout = 1.0 s
  db.py        SQLite: init_db · list_courses              - the CRITICAL dependency
  health.py    GET /health/live · GET /health/ready: checks in parallel, each with a timeout
  metrics.py   Counter · Histogram · Gauge · MetricsMiddleware (route TEMPLATE labels) · /metrics
  main.py      lifespan (draining on shutdown) · /courses · /enrollments/{id} · /reports/{id} · /boom
demos/   common (our app :8056 + a fake payments service :8057) · health · traffic
tests/   conftest · test_health (5) · test_metrics (6) · test_homework56 (3)
```

## Liveness vs readiness
| | `/health/live` | `/health/ready` |
|---|---|---|
| question | is the process alive? | can it serve traffic **now**? |
| checks | **nothing** | database (critical) · payments (non-critical) |
| failing means | restart the container | stop sending traffic, **don't** restart |
| answers | always `200 {"status": "alive"}` | `200 ready` · `200 degraded` · `503 not_ready` · `503 draining` |

```yaml
# Kubernetes
livenessProbe:  {httpGet: {path: /health/live,  port: 8000}, periodSeconds: 10}
readinessProbe: {httpGet: {path: /health/ready, port: 8000}, periodSeconds: 5}
```

## Metrics
| type | example | use |
|---|---|---|
| Counter – only goes up | `http_requests_total{method, route, status}` · `enrollments_total{course}` | rates, error rate |
| Histogram – buckets | `http_request_duration_seconds{method, route}` | average, p95 / p99 |
| Gauge – up and down | `http_requests_in_progress` | right now |

```yaml
# prometheus.yml
scrape_configs:
  - job_name: course-hub
    scrape_interval: 15s
    static_configs: [{targets: ["course-hub:8000"]}]
```
```promql
sum(rate(http_requests_total[5m]))                                             # requests per second
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))   # error rate
histogram_quantile(0.95, sum by (le, route) (rate(http_request_duration_seconds_bucket[5m])))  # p95
```

## Rules
- Liveness checks **nothing** – a broken database must not make Kubernetes restart every pod.
- Readiness checks what you **need**, in parallel, each with a **timeout** – a health check must be fast.
- Non-critical dependencies → `degraded`, still 200 – don't take yourself out because a partner is slow.
- On shutdown answer 503 `draining` first, so the load balancer stops sending new requests.
- Labels: the **route template**, never the raw URL or a user id – every label value is a new series.
- Don't measure `/metrics` and `/health` – the scrapers would be most of your traffic.
- One shared HTTP client – creating one per check made each check ~50 ms instead of ~3 ms.

## Interview questions
1. **What is the difference between liveness and readiness?** Liveness asks "is the process alive?" – if it fails, the platform restarts the container, so it checks nothing external. Readiness asks "can it serve traffic now?" – it checks critical dependencies; if it fails, the instance is taken out of the load balancer but not restarted.
2. **Counter, gauge or histogram?** A counter only goes up (requests, errors) – you look at its rate. A gauge goes up and down (requests in progress, queue length). A histogram counts observations in buckets (latency), so you can compute averages and percentiles like p95.
3. **What is high cardinality and why avoid it?** Every unique combination of label values is a separate time series. Labels like a raw URL with ids, a user id or an email create millions of series and overload Prometheus. Use bounded values like the route template and the status code.

## Homework
1. **A Redis check:** add `check_redis()` (critical) with `PING` – `fakeredis` in the tests.
2. **An info metric:** `app_info{version="1.4.0"} 1` (a Gauge set to 1), so dashboards show which version runs.
3. Tests for both.

Answer at the start of Video 57 (Docker).

## Homework answer (shown at the start of Video 57)
**1. A Redis check (critical).** `config.py` gets `redis_url`; `health.py` gets
```python
async def check_redis() -> None:
    client = aioredis.Redis.from_url(get_settings().redis_url)     # import redis.asyncio as aioredis
    try:
        await client.ping()
    finally:
        await client.aclose()
```
and one line in `CHECKS`: `"redis": (check_redis, True)`. It runs in parallel with the others and gets the same 1 s timeout.
Real run: Redis up → `200 ready`, redis `up` in 4.2 ms; `redis-cli shutdown` → `503 not_ready`,
`ConnectionError: Error 111 connecting to 127.0.0.1:6379. Connection refused.` in 2.5 ms.

**2. An info metric.** `APP_INFO = Gauge("app_info", "Which version is running", ["version"])`, set once in the
lifespan: `APP_INFO.labels(get_settings().version).set(1)` → `app_info{version="1.4.0"} 1.0`.
The value is always 1 – the label carries the information, so a dashboard can show "1.4.0", and during a
deploy you see two versions side by side.

**3. Tests:** `tests/test_homework56.py` – 3 tests; the conftest swaps Redis for `fakeredis.FakeAsyncRedis`.
`pytest` → **14 passed**.
