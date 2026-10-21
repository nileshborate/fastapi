# Video 5 – Async/Await and the Event Loop

**Async helps when your code is WAITING** (database, API calls, files). It does not make CPU-heavy work faster.

## Files
| File | What it shows |
|------|---------------|
| `sync_vs_async.py` | Same job: sync takes ~3s, async with `asyncio.gather` takes ~1s; what a coroutine is |
| `main.py` | FastAPI endpoints: `def`, `async def`, and the blocking mistake |
| `load_test.py` | Sends 10 requests at once to each endpoint and times them |
| `homework.py` | Convert to async and make it ~1s |

## Run
```bash
pip install -r requirements.txt
python sync_vs_async.py
fastapi dev main.py          # terminal 1
python load_test.py          # terminal 2
```
Expected:
```
/sync      10 requests at once ->  1.1s   (def runs in a thread pool)
/async     10 requests at once ->  1.0s   (event loop serves others while waiting)
/blocking  10 requests at once -> 10.0s   (time.sleep inside async def blocks everything!)
```

## Rules for FastAPI
| Your code inside the endpoint | Use |
|-------------------------------|-----|
| Async libraries (`await` httpx, asyncpg, `asyncio.sleep`) | `async def` |
| Blocking libraries (`requests`, `time.sleep`, most sync DB drivers) | plain `def` |
| Not sure | plain `def` is the safe choice |
| Heavy CPU work (image processing, ML training) | background worker / separate process |

## Key words
- **Coroutine** – what `async def` returns; it runs only when awaited.
- **await** – "pause me here, let the event loop run other tasks until this is ready".
- **Event loop** – one thread that switches between waiting tasks.
- **Concurrency** – handling many tasks by switching while they wait. **Parallelism** – doing many tasks at the same instant on multiple CPU cores.

## Interview questions
1. **When does async help, and when doesn't it?** It helps I/O-bound work (waiting on network, DB, files). It doesn't speed up CPU-bound work.
2. **`def` vs `async def` in FastAPI?** `def` endpoints run in a thread pool; `async def` endpoints run on the event loop. Never call blocking code inside `async def`.
3. **Concurrency vs parallelism?** Concurrency = many tasks in progress by switching while they wait. Parallelism = many tasks executing at the same instant on multiple cores.

## Homework
Open `homework.py` (takes ~3s). Convert it to async with `asyncio.gather` so it finishes in ~1s. Answer at the start of Video 6.
