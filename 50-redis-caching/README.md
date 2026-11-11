# 50 – Caching with Redis, Part 1: cache-aside + TTL

**Video 50** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project – a fake **slow database** (every query takes 0.3 s and is counted) and a
real **Redis**. The same course read 20 times: **1** database query instead of 20, about **2 ms**
instead of 300 ms. The **cache-aside** pattern, **TTL** (keys that expire by themselves), deleting
the cached copy when the data changes, and an API that keeps working when Redis is down.

## Run it
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine   # Redis 7 on port 6379
cd 50-redis-caching
pip install -r requirements.txt
python -m demos.basics      # SET · GET · EX · TTL (-1, -2) · INCR · decode_responses
python -m demos.speed       # 20 reads: 1 query vs 20 · 50 users at once: a stampede (Part 2)
python -m demos.stale       # stale data · the TTL ends · PATCH deletes the key · X-Cache-TTL
python -m demos.down        # Redis down: 200 MISS (slower) · /health/redis -> 503
fastapi dev app/main.py     # http://localhost:8000/docs - watch the X-Cache header
pytest                      # 6 passed (fakeredis - no Redis needed)
```

## Project
```
app/
  config.py            redis_url · course_ttl=60 · stats_ttl=30 · db_delay=0.3
  db.py                a fake slow database: fetch_course · save_course · popular_stats · queries
  deps.py              get_redis -> request.app.state.redis (one client, one connection pool)
  cache.py             course_key() · cache_get / cache_set / cache_delete (a failing Redis = a MISS)
  routers/courses.py   GET /courses/{id} (cache-aside) · PATCH /courses/{id} (DB, then DELETE key)
  routers/stats.py     GET /stats/popular - cached 30 s, X-Cache-TTL
  main.py              lifespan: Redis.from_url(..., decode_responses=True) · aclose() · /health/redis
demos/   basics · speed · stale · down   (uvicorn in its own thread, port 8050)
tests/   conftest (fakeredis) · test_courses
```

## Cache-aside (lazy loading)
```
GET  -> 1. GET course:3 from Redis -> found?  HIT: return it (no database)
                                   -> None?   MISS: 2. ask the database
                                                    3. SET course:3 <json> EX 60
                                                    4. return it
PATCH -> 1. write the database   2. DEL course:3   (the next GET is a MISS -> fresh data)
```

| Measured (demos.speed) | with the cache | without |
|---|---|---|
| 20 reads of one course | 0.37 s · 1 query | 6.09 s · 20 queries |
| one read | MISS 330 ms, then HIT ~2 ms | ~300 ms every time |

## Rules
- Cache **reads that are slow and repeated** – and data that may be a little old.
- Always set a **TTL** (`ex=`): even if you forget to delete a key, it fixes itself.
- On a write: update the **database first, then delete** the key (don't update the cached copy).
- Keys in **one place**: `course:3`, `stats:popular`. Never `KEYS *` in production (it blocks Redis).
- Redis is a **cache, not the source of truth**: if it fails, log it and use the database.
- `decode_responses=True` → `str` instead of `bytes`. Store JSON: `model_dump_json()` / `model_validate_json()`.
- One client for the app (lifespan) – it holds a **connection pool**; close it with `aclose()`.

## Interview questions
1. **What is the cache-aside pattern?** The application checks the cache first; on a miss it reads the database, stores the result in the cache with a TTL, and returns it. On a write it updates the database and deletes the cached key, so the next read loads fresh data.
2. **Why is TTL important, and what are TTL -1 and -2 in Redis?** A TTL makes keys expire by themselves: it limits stale data and memory use, even when an invalidation is missed. `TTL` returns the seconds left, `-1` for a key without an expiry, `-2` for a key that doesn't exist.
3. **What happens to your API if Redis goes down?** With cache-aside done right, nothing breaks: cache errors are caught and logged, requests go to the database (slower), and a health check reports Redis as down (503) so monitoring can alert.

## Homework
1. **Cache the list:** `GET /courses` (all courses) cached under `courses:all` for 60 s – and `PATCH` must delete it too.
2. **A cache-clear endpoint:** `DELETE /cache/courses/{id}` → 204, deletes `course:{id}`.
3. Tests for both.

Answer at the start of Video 51 (Caching with Redis Part 2).
