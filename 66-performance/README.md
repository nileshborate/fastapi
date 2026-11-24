# 66 – Performance and load testing: how many users can Course Hub really handle?

**Video 66** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

"It's fast on my laptop" says nothing. Today 50 – 800 simulated visitors hit the real server with
**Locust**: they open the course list, then one course, again and again. We measure median, p95 and requests per
second, find what breaks first, fix it, and run the test again.

Course Hub **1.15.0** (Video 65 + its homework):
```
your machine: locust (50 ... 800 "visitors") ──https──▶ nginx ──▶ api (2 uvicorn workers) ──▶ db
                                                          └── no rate limit for THIS ip only (geo)
the numbers: Locust's report (client side) + Prometheus (server side, Video 65)
```

## Run a load test
```bash
pip install -r loadtest/requirements.txt         # locust - on YOUR machine, not in the api image
# a STAGING server - never production: the seed writes 2,000 courses
ssh deploy@staging.example.com 'cd coursehub && docker compose exec -T db psql -U coursehub coursehub' \
    < loadtest/seed.sql
locust -f loadtest/locustfile.py --host https://staging.example.com --headless -u 50 -r 10 -t 60s
```
`-u` visitors · `-r` new visitors per second · `-t` how long. Without `--headless`: a web UI on :8089 with live charts.
**Before you test:** put your test machine's IP into the `geo $loadtest` block in `nginx/default.conf` – or nginx's
rate limit answers instead of your api (finding 1). Remove it afterwards.

## On your laptop
```bash
cd 66-performance
cp .env.example .env && ./scripts/make-certs.sh
docker compose up -d --build --wait
pip install -r requirements-dev.txt
pytest --cov                               # 76 passed · coverage 98.97 %
```

## Project – what's new
```
loadtest/locustfile.py      a Visitor: 5 × /courses · 3 × /courses/{id} · 1 × /health/ready, 0.5 – 1.5 s apart
loadtest/seed.sql           2,000 courses - a real-sized table (staging only!)
app/main.py, app/db.py      GET /courses?limit=50&offset=0 - a page, at most 200 (was: the whole table)
compose.yaml                WEB_CONCURRENCY=2 (uvicorn workers) · PROMETHEUS_MULTIPROC_DIR on a tmpfs
app/metrics.py              2 workers: every worker writes its numbers to that folder, /metrics adds them up
nginx/default.conf          geo $loadtest: no rate limit for the test machine · the zone has a NEW name
deploy/rollout.sh           after "nginx -s reload": nginx's log has [emerg]? -> red, the old config stays
tests/                      76 tests: + pagination, shared metrics, the allow-list, the reload check
```

## Honest note – how I ran it
The stand-in lab from Videos 62 – 65. The server is a container with **2 CPU cores** – and Locust ran on the SAME
machine, so the load generator and the server shared those 2 cores. The numbers are real, but they're numbers of
MY setup: compare them with each other (before/after), not with your server. Locust never reported its own CPU as
a problem (it warns above 90 %).

## What the runs showed – real numbers
Every run: 60 s. `req/s` = requests per second. Times in milliseconds.

| run | version | visitors | requests | failed | median | p95 | req/s | api CPU |
|---|---|---|---|---|---|---|---|---|
| 1 through the rate limit | 1.14.0 | 50 | 2,880 | **2,269 × 429** | 1 | 17 | 48.8 | – |
| 2 baseline (the whole table) | 1.14.3 | 50 | 2,828 | 0 | 13 | 32 | 47.9 | 38.6 % |
| 3 /courses = one page | 1.14.4 | 50 | 2,854 | 0 | **5** | **10** | 48.3 | **11.9 %** |
| 4 + 2 workers | 1.14.5 | 50 | 2,815 | 0 | 6 | 50 | 47.7 | 13.5 % |
| 5 shared metrics | 1.15.0 | 50 | 2,840 | 0 | 6 | 50 | 48.1 | 12.6 % |
| 6 | 1.15.0 | 100 | 5,648 | 0 | 7 | 52 | 95.6 | – |
| 7 | 1.15.0 | 200 | 11,265 | 0 | 10 | 56 | 190.7 | 47.6 % |
| 8 | 1.15.0 | 400 | 21,154 | 0 | 38 | 98 | 357.8 | 90.4 % |
| 9 | 1.15.0 | 800 | 29,563 | 0 | **440** | **990** | 491.5 | 125 % |
| 10 the same, **1 worker** | 1.15.0 | 400 | 20,302 | 0 | 43 | 300 | 343.0 | 77.3 % |
| 11 the same, **1 worker** | 1.15.0 | 800 | 19,086 | 0 | **1,400** | **1,800** | 317.2 | 88.2 % |

**The answer:** up to ~400 visitors (~360 requests a second) p95 stays under 100 ms. At 800 the server is full –
both cores busy, p95 almost 1 s (our SlowRequests alert says 0.5 s) – but still **0 errors**: requests wait, they
don't fail. Not one failed request in 11 runs after the rate limit was out of the way.

### Finding 1 – my first load test measured nginx, not the api
2,269 of 2,880 requests: **429 Too Many Requests** – Video 61's `limit_req` (10 a second per IP, burst 20). One
load generator = ONE IP, so to nginx 50 visitors look like one very busy user. Fix: `geo $loadtest` – the test
machine's IP gets an empty key, and an empty key is never counted. Only that IP, only while testing.

### Finding 2 – the allow-list was green, and never loaded
My first try changed only the KEY of the `perip` zone. `nginx -t` said OK, the deploy was green – and run 2 still had
**2,247 × 429**. nginx's own log:
```
[emerg] 1#1: limit_req "perip" uses the "$perip_key" key while previously it used the "$binary_remote_addr" key
```
A shared memory zone can't change its key on a reload – nginx refuses the new config and keeps the OLD one. `nginx -s
reload` only sends a signal, so nobody saw it; even homework 64's "5 of 5 through nginx" passed (the old config
works fine). Now rollout.sh reads nginx's log after every reload: `[emerg]` → red, "nginx refused the new config".
It caught exactly this on the next try (1.14.2: deploy red in 41 s). With a NEW zone name (`visitors`): green.

### Finding 3 – /courses sent the whole table: 700 kB per click
`GET /courses` returned all 2,000 courses: **700,455 bytes**. One page of 50: **17,351 bytes**. Same 50 visitors:
p95 32 → **10 ms**, the api's CPU 38.6 % → **11.9 %**. The biggest win of the day was not a server setting – it
was sending less. (A breaking change: old clients get 50 courses now – `?limit=200&offset=…` for more.)

### Finding 4 – 2 workers: worse at 50 visitors, much better at 800
uvicorn runs ONE Python process – one CPU core. `WEB_CONCURRENCY=2`: two processes. At 50 visitors that made p95
WORSE (10 → 50 ms): nothing was waiting, and the two processes competed with nginx, the database and Locust for the
same 2 cores. Under real load, the opposite (runs 10/11 vs 8/9):

| visitors | 1 worker | 2 workers |
|---|---|---|
| 400 | p95 300 ms · 343 req/s | p95 **98 ms** · 358 req/s |
| 800 | p95 1,800 ms · 317 req/s · CPU stuck at ~88 % (one core) | p95 **990 ms** · **491 req/s** · 125 % |

Rule: workers = CPU cores – and measure at the load you expect, not at "a few users".

### Finding 5 – with 2 workers, /metrics jumped back and forth
Each worker counts on its own; a scrape reaches ONE of them. The `/courses` counter, read 6 times in a row:
`621 · 621 · 621 · 621 · 963 · 621` – Prometheus would see resets and draw nonsense. Now every worker writes into
`PROMETHEUS_MULTIPROC_DIR` (a tmpfs – empty at every start) and `/metrics` adds them up: `1610` six times.

## Interview questions
1. **What do p50, p95 and p99 mean – and why not the average?** p95 = 95 % of requests were faster than this. The
   average hides the slow ones: 99 fast requests and one of 10 s look "fine" on average. Users feel the tail.
2. **How many uvicorn workers?** About one per CPU core: one Python process uses one core (the GIL). More than the
   cores: they fight for the CPU. And measure – at low load more workers can even be slower.
3. **What can make a load test lie?** A rate limit (you measure nginx), a load generator on the same machine or too
   weak, an empty test database, testing production instead of staging, and a run too short to warm up.

## Homework
1. **A micro-cache:** nginx `proxy_cache` for `GET /courses` – 5 seconds. Measure 800 visitors again.
2. **Step by step:** a `LoadTestShape` in the locustfile – 100, 200, 400, 800 visitors, 30 s each – and find where
   p95 crosses 500 ms.
3. **A load test that fails:** the run exits with code 1 if p95 > 500 ms or more than 1 % of the requests fail
   (Locust's `quitting` event: `environment.process_exit_code`).

Answer at the start of Video 67.

## Homework answer (shown at the start of Video 67)
**1. A micro-cache** – `nginx/default.conf`: `proxy_cache_path … keys_zone=courses:10m inactive=1m`, and in
`location = /courses`: `proxy_cache courses` · `proxy_cache_valid 200 5s` · `proxy_cache_lock on` (100 misses at
once → ONE request to the api) · `proxy_cache_use_stale updating`. The cache lives on a tmpfs (`compose.yaml`).
An `X-Cache` header says HIT / MISS / EXPIRED.
**2. Step by step** – `loadtest/steps.py`: a `LoadTestShape`, 100 → 200 → 400 → 800 visitors, 30 s each.
**3. A load test that can fail** – the `quitting` event in the locustfile: p95 > 500 ms or > 1 % failed →
`environment.process_exit_code = 1` and `!!! FAILED: …`. 2 new tests: **78 passed**, coverage 98.97 %.

**The first try failed – and that was good.** I put `add_header X-Cache …` INSIDE `location = /courses`. The
Video 62 test went red: `test_security_headers_only_on_the_server`. An `add_header` in a location throws away ALL
the server's `add_header`s – HSTS & co. would have disappeared from /courses. Now it sits at server level:
```
$ curl -sD - -o /dev/null https://coursehub.example.com/courses      (3 times)
strict-transport-security: max-age=31536000  · x-cache: MISS
strict-transport-security: max-age=31536000  · x-cache: HIT
strict-transport-security: max-age=31536000  · x-cache: HIT
```
**How stale?** POST a new course → 201 → the list: still the old one (`HIT`) → 6 s later: `11 courses, the last:
Brand-new course` (`EXPIRED`). At most 5 s old – fine for a course list, never for a bank balance.

**The runs** (the same stand-in lab: 2 cores, Locust on the same machine, nginx 1.28, 2 uvicorn workers):

| run | p95 | req/s | failed | exit code |
|---|---|---|---|---|
| 800 visitors, no cache | 580 ms | 572.5 | 0 | 0 |
| 800 visitors, **micro-cache** | **88 ms** (/courses: 46 ms) | **720.8** | 0 | 0 – `OK: p95 88 ms` |
| steps 100 / 200 / 400 / 800 (cache) | 48 / 50 / 52 / 74 ms | – | 0 | 0 – never crossed 500 ms |
| 1,600 visitors (cache) | **1,500 ms** | 947.4 | **1.3 %** | **1** – `!!! FAILED: p95 1500 ms (max 500) · 1.3% failed` |

In the cached minute Locust sent **23,663** `GET /courses` – the api's log shows **11**. One request every ~5 s;
nginx answered the rest. The 1,600 run is the point of homework 3: a script or CI can now SEE "too slow".
