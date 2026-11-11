# 49 – Streaming Responses and Server-Sent Events

**Video 49** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project – no database – about sending data **piece by piece**: a 1,000,000-row CSV
download with `StreamingResponse` (0.5 MB of memory instead of 107 MB), `FileResponse` with **Range**
requests, **JSON Lines** from a generator, and **Server-Sent Events** (`fastapi.sse`, FastAPI 0.135+):
live job progress, resume with `Last-Event-ID`, an AI-style chat answer over POST, and what happens
when the user closes the tab.

## Run it
```bash
cd 49-streaming-sse
pip install -r requirements.txt
python -m demos.download       # buffered vs streamed: first byte + peak memory · FileResponse + Range
python -m demos.sse            # the text/event-stream wire format · Last-Event-ID · chat over POST
python -m demos.disconnect     # the tab closes after 2 events - the server stops the job
fastapi dev app/main.py        # http://localhost:8000 - a live progress bar (EventSource)
pytest                         # 9 passed
```

## Project
```
app/
  data.py              csv_rows (one line) · csv_chunks (1,000 lines) · slow_lessons (async)
  routers/files.py     /export/buffered · /export/streamed · /export/line-by-line · /files/report
  routers/live.py      /lessons/stream (JSON Lines) · /jobs/{job}/progress (SSE) · POST /chat/stream (SSE)
  static/live.html     new EventSource(...) · addEventListener("progress" | "done")
  main.py              lifespan: writes a report file to disk for FileResponse
demos/   download · sse · disconnect   (uvicorn in its own thread, port 8049)
tests/   test_files · test_live
```

## Which response?
| You have | Use | On the wire |
|---|---|---|
| a big result you create step by step | `StreamingResponse(generator)` – yield **chunks**, not tiny lines | the bytes, as they come |
| a file on disk | `FileResponse(path)` – chunks, `Content-Length`, `ETag`, **Range** (206) | the file |
| items for a program | `yield` with **no** `response_class` → **JSON Lines** | `application/jsonl` – one JSON per line |
| live updates for a browser | `response_class=EventSourceResponse` + `yield ServerSentEvent(...)` | `text/event-stream` |

## Server-Sent Events
```
event: progress                                 <- addEventListener("progress", ...)
data: {"job": "export-1", "step": 3, ...}       <- always JSON (raw_data: as it is, e.g. [DONE])
id: 3                                           <- the browser sends it back: Last-Event-ID: 3
retry: 3000                                     <- reconnect after 3 s
<blank line = the end of one event>
```
FastAPI adds `Cache-Control: no-cache`, `X-Accel-Buffering: no` (Nginx), and a `: ping` comment
every 15 s when nothing is sent. SSE is **one-way** (server → client) over plain HTTP – for two-way
messages, use WebSockets (Videos 46, 47).

## Rules
- Stream **big** results – a buffered response holds the whole body in memory (107 MB vs 0.5 MB here).
- Yield **chunks** (e.g. 1,000 lines): a **sync** generator is read in the threadpool – one thread hop per item.
- A stream has **no `Content-Length`** – the browser can't show "x of y MB". A file on disk can.
- Use `finally:` in a stream – it runs when the client leaves, so you can stop work and clean up.
- Always validate stream parameters (`count`, `rows`, `delay`) – a stream can run for a long time.

## Interview questions
1. **When do you use `StreamingResponse` instead of a normal response?** When the body is big or produced over time: CSV/Excel exports, large files, AI answers, logs. The client gets the first bytes immediately and the server never holds the whole body in memory.
2. **What are Server-Sent Events and how do they differ from WebSockets?** SSE is a one-way stream from server to client over normal HTTP (`text/event-stream`), with automatic reconnection and `Last-Event-ID` built into the browser's `EventSource`. WebSockets are two-way and use their own protocol after an upgrade.
3. **How do you serve large files efficiently in FastAPI?** With `FileResponse`: it reads the file in chunks, sets `Content-Length`, `ETag` and `Last-Modified`, and supports **Range** requests (206 Partial Content) so downloads can resume.

## Homework
1. **A clock:** `GET /clock?count=5` – SSE with `event: tick` and the server time once per second, `count` between 1 and 60, then `event: done`.
2. **Resume JSON Lines:** `GET /lessons/stream?after=3` starts with lesson 4.
3. Tests for both.

Answer at the start of Video 50 (Caching with Redis Part 1).
