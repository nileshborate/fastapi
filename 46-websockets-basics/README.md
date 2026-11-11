# 46 – WebSockets Part 1: Real-Time Basics

**Video 46** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project – no database – about **real time**: in HTTP the client always speaks first.
With a **WebSocket**, one connection stays open and **the server can send whenever it wants**.
We build an echo socket, a **live classroom** with a **ConnectionManager**, an HTTP endpoint that
pushes to every open socket, a tiny browser client, and tests with FastAPI's TestClient.

## Run it
```bash
cd 46-websockets-basics
pip install -r requirements.txt
python -m demos.polling        # the old way: ask again and again - 6 requests for 1 message
python -m demos.echo           # 101 Switching Protocols - then many messages on one connection
python -m demos.classroom      # two students, a chat, an error, an announcement, a goodbye
fastapi dev app/main.py        # open http://localhost:8000 in TWO browser windows
pytest                         # 8 passed
```

## Project
```
app/
  main.py               the app + GET / (the browser client)
  manager.py            ConnectionManager: connect · disconnect · names · broadcast
  schemas.py            ChatIn (1-500 characters) · Announcement · Delivered
  routers/echo.py       WS /ws/echo                - accept · receive_text · send_text
  routers/classroom.py  WS /ws/class/{name}        - join · chat · leave (broadcast)
                        POST /announcements · GET /online
  static/classroom.html new WebSocket(...) · onmessage · send
demos/   polling · echo · classroom   (a real uvicorn server on port 8046)
tests/   test_echo · test_classroom   (client.websocket_connect)
```

## The life of a WebSocket
```
client: GET /ws/echo  Upgrade: websocket      ->  server: 101 Switching Protocols
        ... now both sides can send at any time, on the same connection ...
await websocket.accept()          say yes to the upgrade (before that: nothing works)
await websocket.receive_text()    wait for the next message - without blocking the server
await websocket.send_text(...)    send - also send_json / receive_json / send_bytes
except WebSocketDisconnect:       the client closed the tab (code 1000, 1001, ...)
```

## Rules
- **`accept()` first** – then a `while True` loop around `receive_*`. The loop ends with `WebSocketDisconnect`.
- **Messages are input** – validate them with Pydantic like a request body; a bad message gets an **error message**, not a crash.
- A **bad path or query parameter** is refused before `accept`: a real client gets **HTTP 403**, the TestClient sees close code **1008** (policy violation).
- The **ConnectionManager** lives in **one process**. Several workers or servers? Use Redis pub/sub (later).
- Polling = many requests, mostly empty, always a bit late. WebSockets = one connection, instant pushes.

## Interview questions
1. **What is a WebSocket and how is it different from HTTP?** A long-lived, two-way connection. It starts as an HTTP request with `Upgrade: websocket`; the server answers **101 Switching Protocols**. After that both sides can send messages at any time – in HTTP only the client starts a conversation.
2. **How do you handle a WebSocket in FastAPI?** `@app.websocket("/path")` with a `WebSocket` parameter: `await websocket.accept()`, then a loop with `receive_text/json` and `send_text/json`, and `except WebSocketDisconnect` for cleanup.
3. **What does a connection manager do – and what is its limit?** It keeps the open connections (and who they are), so you can send to one or **broadcast** to all, and removes them on disconnect. It lives in the memory of one process – with several workers you need a shared channel like Redis pub/sub.

## Homework
1. **Private messages:** `{"to": "Ravi", "text": "..."}` goes only to Ravi (and back to the sender). Ravi not online → an error message.
2. **No two Ashas:** a name that is already in the class: accept, then close with code **1008** and the reason `"name taken"`.
3. Tests for both.

Answer at the start of Video 47 (WebSockets Part 2).
