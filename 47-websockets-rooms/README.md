# 47 – WebSockets Part 2: Rooms and Authentication

**Video 47** of *FastAPI Mastery: Zero to Production* – Nilesh Technology
▶️ Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

A fresh, small project (users in memory, no database) that grows the live classroom of Video 46 into
**chat rooms** – one room per course – with **authentication over WebSockets**: a JWT in the query
string, checked **before** `accept`, rooms only for **enrolled** users, a connection that **closes
when the token expires**, a teacher who **announces to one room** over HTTP, and tests for all of it.

## Run it
```bash
cd 47-websockets-rooms
pip install -r requirements.txt
cp .env.example .env
python -m demos.auth           # no token / bad token / not enrolled: 403 · a 3-second token: closed 1008
python -m demos.rooms          # python and sql rooms - a message only reaches its own room
fastapi dev app/main.py        # /docs: POST /token, members, announcements
pytest                         # 11 passed
```
Users (all with the password `blue-river-42`): **asha** (python, sql) · **ravi** (python) ·
**meera** (sql) · **nilesh** (teacher: python, sql, fastapi).

## Project
```
app/
  config.py           JWT_SECRET · ACCESS_TOKEN_MINUTES
  security.py         Argon2 · create_access_token(username, lifetime) · decode_access_token
  users.py            USERS (in memory): role + the rooms each user may join
  deps.py             get_current_user (HTTP header) · ws_session (?token=..., before accept)
  rooms.py            RoomManager: join · leave · members · count · broadcast(room, ...)
  routers/auth.py     POST /token
  routers/rooms.py    WS /ws/rooms/{room}?token=...
                      GET /rooms/{room}/members · POST /rooms/{room}/announcements (teacher)
demos/   auth · rooms   (a real uvicorn server on port 8047)
tests/   test_ws_auth · test_rooms
```

## Auth over WebSockets
```
browser: new WebSocket(url)       -> can NOT set an Authorization header
so:      ws://.../ws/rooms/python?token=eyJ...      (or a cookie, or the first message)

before accept:  bad / missing token, not enrolled  -> WebSocketException(1008)
                real client: the handshake fails, HTTP 403 · TestClient: code 1008 + reason
after accept:   the token expires                  -> close(1008, "token expired")
```

## Rules
- **Check the token before `accept`** – a bad client never gets an open connection.
- A token in the URL can end up in **server logs** – keep it **short-lived**, always use **wss://**.
- A JWT is checked **once** at connect – a long connection must **end when the token expires**
  (`asyncio.wait_for(..., timeout=seconds_left)`).
- **Authorization per room**: a valid token is not enough – the user must be enrolled.
- `finally:` – leave the room in **every** case: closed tab, expired token, error.
- Still **one process** – several workers need Redis pub/sub (later in the course).

## Interview questions
1. **How do you authenticate a WebSocket in FastAPI?** Browsers can't send an `Authorization` header with a WebSocket, so the token comes as a query parameter (or a cookie, or the first message). A dependency validates it **before `accept`** and raises `WebSocketException(code=1008)` if it's bad.
2. **How do you build chat rooms?** Keep a dictionary `room -> connections`; join adds, leave removes (and deletes empty rooms), and broadcast sends only to the connections of one room.
3. **What happens when the JWT expires during an open WebSocket?** Nothing – unless you handle it. The token is checked only at the handshake, so the server must close the connection when `exp` is reached (for example with `asyncio.wait_for` and a timeout), and the client logs in again.

## Homework
1. **History:** a new member gets the **last 20 messages** of the room right after joining (`collections.deque(maxlen=20)` per room).
2. **Remove a student:** `DELETE /rooms/{room}/members/{username}` (teacher only) closes all of that user's connections in the room with code **1008** and the reason `"removed by teacher"`.
3. Tests for both.

Answer at the start of Video 48 (Async Deep Dive: def vs async def).
