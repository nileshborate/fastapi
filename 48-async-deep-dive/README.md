# 48 – Async Deep Dive: def vs async def

**Video 48** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project – no database – that **measures** what really happens with `def` and
`async def`: the **event loop**, the **threadpool** (40 threads), a **blocking call** that freezes the
whole server, `run_in_threadpool`, and CPU work in **another process** – with real timings.

## Run it
```bash
cd 48-async-deep-dive
pip install -r requirements.txt
python -m demos.waiting        # 10 x 0.5 s of waiting: 0.5 s - or 5 s with time.sleep in async def
python -m demos.frozen         # GET /ping while a slow request runs: 0.00 s - or 1.9 s
python -m demos.threads        # who runs my endpoint? 40 threads: 40 requests vs 41 vs 80
python -m demos.cpu            # CPU work: inline vs a thread (GIL) vs a process
fastapi dev app/main.py
pytest                         # 7 passed
```

## Project
```
app/
  work.py            slow_report (blocking I/O) · count_primes (CPU) · thread_name()
  routers/io.py      /io/async-await · /io/async-blocking (BAD) · /io/sync · /io/offload
  routers/cpu.py     /cpu/inline (BAD) · /cpu/thread · /cpu/process
  main.py            lifespan: a ProcessPoolExecutor · GET /ping · GET /threadpool
demos/   waiting · frozen · threads · cpu   (uvicorn in its own thread, port 8048)
tests/   test_concurrency                   (httpx.AsyncClient + ASGITransport)
```

## The rules
| You write | FastAPI runs it | Blocking code inside? |
|---|---|---|
| `async def` | **on the event loop** (one thread) | ❌ **freezes every request** – use `await` with async libraries |
| `def` | **in the threadpool** (40 threads) | ✅ fine – blocks only one worker thread |
| `async def` + `await run_in_threadpool(f, ...)` | the loop, `f` in a worker thread | ✅ the async way to call blocking code |
| CPU-heavy work | – | threads don't help (the **GIL**) → `ProcessPoolExecutor` or a task queue |

- **Blocking** = waits without `await`: `time.sleep`, `requests.get`, a sync database driver, `open().read()` of a big file, heavy math.
- `async def` only helps if the slow parts are **awaited**. No `await` inside? A plain `def` is safer.
- The threadpool has **40 threads** (`anyio.to_thread.current_default_thread_limiter()`): request 41 waits for a free thread.
- The same rules apply to **dependencies**: `def` dependencies run in the threadpool too.

## Interview questions
1. **What is the difference between `def` and `async def` endpoints in FastAPI?** `async def` runs directly on the event loop – fast, but a blocking call inside it freezes the whole server. `def` runs in a threadpool (40 threads by default), so blocking calls only block one worker thread.
2. **How do you call blocking code from an `async def` endpoint?** Use an async library if there is one (`httpx.AsyncClient`, `asyncpg`); otherwise `await run_in_threadpool(func, ...)` (or `asyncio.to_thread`), which runs it in a worker thread while the loop stays free.
3. **Why don't threads speed up CPU-heavy Python code?** Because of the GIL: only one thread runs Python code at a time. CPU work needs separate processes – a `ProcessPoolExecutor`, more workers, or a task queue like Celery.

## Homework
1. **A legacy report:** `GET /reports/{n}` calls `slow_report(1.0)` from an `async def` endpoint – without freezing the server. A test: while 5 reports run, `GET /ping` answers in under 0.1 s.
2. **A smaller threadpool:** set the threadpool to **10 threads** in the lifespan, and show in a test that 10 `def` requests run together but the 11th waits for a second round.
3. Tests for both.

Answer at the start of Video 49 (Streaming Responses and Server-Sent Events).
