# 51 – Caching with Redis, Part 2: the stampede, a cache decorator, more Redis types

**Video 51** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project – the same slow fake database (0.3 s per query, counted) and a real
Redis. Part 1 ended with a **cache stampede**: 50 users, an empty key, **50** database queries.
Here a **lock** (`SET NX EX` + a safe Lua release) brings it down to **1**. Then **TTL jitter**,
one reusable `get_or_set()` and a `@cached(...)` **decorator** with `.invalidate()`, and three more
Redis types – **hash**, **sorted set**, **list** – written together with a **pipeline**.

## Run it
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
cd 51-redis-caching-part2
pip install -r requirements.txt
python -m demos.stampede    # 50 at once: no lock = 50 queries · a lock = 1 (1 MISS + 49 WAIT)
python -m demos.jitter      # ex=60 -> all 60 · with_jitter(60) -> 60..66
python -m demos.types       # HSET/HINCRBY · ZADD/ZINCRBY/ZRANGE · LPUSH/LTRIM · a pipeline
python -m demos.views       # the API: views -> counters, a leaderboard, recently viewed
fastapi dev app/main.py     # http://localhost:8000/docs
pytest                      # 8 passed (fakeredis[lua] - no Redis needed)
```

## Project
```
app/
  cache.py             with_jitter · get_or_set (lock, wait, fallback) · @cached + .invalidate
  services.py          @cached("course:{course_id}", ttl=60) async def get_course(redis, course_id)
  routers/courses.py   GET /courses/{id} (X-Cache from a ContextVar) · PATCH -> .invalidate()
  routers/views.py     POST /courses/{id}/views (pipeline) · /courses/{id}/stats · /popular · /users/{u}/recent
  routers/naive.py     Part 1's cache-aside, no lock - only for the stampede demo
  config.py · db.py · deps.py · main.py
demos/   stampede · jitter · types · views   (uvicorn in its own thread, port 8051)
tests/   conftest (fakeredis) · test_cache (anyio) · test_api
```

## The stampede and the lock
```
key empty -> 50 requests -> SET lock:course:3 <token> NX EX 5
   1 request:  OK   -> MISS: ask the database, SET course:3 ... EX 60+jitter, release the lock
  49 requests: None -> WAIT: every 50 ms GET course:3 -> found: return it (no database)
Redis down / waited 3 s -> SKIP: ask the database (the API never breaks)
```
- `NX` = only if the key does **not** exist – exactly one request gets the lock.
- `EX 5` = a crashed worker can't hold the lock forever.
- The release is a tiny **Lua** script: delete the lock **only if it still holds our token** – check and
  delete in one atomic step, so we never delete another request's lock.

| demos.stampede (50 requests at once) | database queries | X-Cache |
|---|---|---|
| `/naive/courses/3` (Part 1) | **50** | – |
| `/courses/3` (lock) | **1** | 1 MISS · 49 WAIT |
| both again (key exists) | 0 | 50 HIT |

## Redis types
| Type | Commands | Here |
|---|---|---|
| hash | `HSET` · `HINCRBY` · `HGETALL` | `course:3:stats` → `{"views": 5}` |
| sorted set | `ZADD` · `ZINCRBY` · `ZRANGE ... REV WITHSCORES` | `courses:popular` – a leaderboard |
| list | `LPUSH` · `LTRIM 0 4` · `LRANGE 0 -1` | `recent:asha` – the newest 5 |
| pipeline | `redis.pipeline(transaction=True)` | 4 commands, 1 round trip (1,000 INCR: 0.098 s → 0.013 s) |

## Rules
- A popular key + a slow query = protect the rebuild with a **lock** (or at least one per worker).
- Add **jitter** to TTLs: keys created together shouldn't expire together.
- One `get_or_set()` for every cache read – the decorator keeps the cache **out of** your business code.
- Every lock has an **expiry**, and you delete only **your own** lock.
- Counters, leaderboards, "recently viewed": Redis can **own** that data – save it to the database
  later (background jobs: Celery, Videos 52–53).

## Interview questions
1. **What is a cache stampede and how do you prevent it?** Many requests miss the same expired key at the same moment and all hit the database together. Prevent it with a lock (`SET key token NX EX`): one request rebuilds the value, the others wait and read it. TTL jitter and refreshing early also help.
2. **How do you implement a distributed lock with Redis safely?** `SET lock:<name> <random token> NX EX <seconds>`: NX gives one owner, EX frees it if the owner crashes. Release it with a Lua script that deletes the key only if the value is still your token – an atomic check-and-delete.
3. **When would you use a hash, a sorted set or a list in Redis?** A hash for an object with fields or several counters (`HINCRBY`), a sorted set for rankings and leaderboards (scores, `ZRANGE ... REV`), a list for ordered recent items or simple queues (`LPUSH` + `LTRIM`).

## Homework
1. **Likes:** `POST /courses/{id}/likes?user=asha` – each user can like a course **once** (hint: a Redis **set**, `SADD` returns 1 or 0) – and `GET /courses/{id}/stats` shows `likes`.
2. **Cache the leaderboard:** `GET /popular` through `@cached("popular:{n}", ttl=10)`.
3. Tests for both.

Answer at the start of Video 52 (Background Jobs with Celery, Part 1).
