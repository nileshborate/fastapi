# Video 7 – Your First FastAPI App

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | `FastAPI()` app object, `@app.get` routes, returning dicts/lists as JSON, an `async def` route, running with `uvicorn.run` |
| `test_main.py` | Testing routes with `TestClient` (200, 404, 405) |
| `requirements.txt` | `fastapi[standard]` + `pytest` |

## Run it
```bash
# inside your activated .venv
pip install -r requirements.txt

fastapi dev main.py                 # development: auto-reload
# other ways:
uvicorn main:app --reload           # main = file main.py, app = the FastAPI object
python main.py                      # uses uvicorn.run(...) at the bottom of main.py
fastapi run main.py                 # production mode (no reload, listens on 0.0.0.0)
```
Open:
- http://127.0.0.1:8000 → `{"message": "Welcome to Course Hub API"}`
- http://127.0.0.1:8000/about, /courses, /health
- http://127.0.0.1:8000/docs (Swagger UI), /redoc, /openapi.json

Run the tests:
```bash
pytest -v
```

## Key ideas
- **`app = FastAPI()`** – the application object. Uvicorn loads it using the import string `main:app`.
- **`@app.get("/")`** – a *decorator* that registers the function below it for **GET** requests to `/`. The pair *method + path* is a **path operation**.
- Return a `dict` or `list` → FastAPI converts it to **JSON** automatically.
- Unknown path → **404 Not Found**. Known path but wrong method → **405 Method Not Allowed**.
- **Uvicorn** is an **ASGI** server. ASGI is async, so one worker can handle many waiting requests (and WebSockets). WSGI (classic Flask/Django) is synchronous: one request per worker at a time.
- FastAPI is built on **Starlette** (web part) and **Pydantic** (data part).

## Interview questions
1. **What is the difference between ASGI and WSGI?** WSGI is the older synchronous interface: each worker handles one request at a time. ASGI is the asynchronous successor: it supports `async`/`await`, many concurrent connections per worker, WebSockets and long-lived connections. FastAPI is an ASGI framework, run by ASGI servers like Uvicorn.
2. **What does `@app.get("/")` do?** It's a decorator that registers the function as the handler (path operation function) for HTTP GET requests on the path `/`. FastAPI stores it in its routing table and calls it when a matching request arrives.
3. **What does `uvicorn main:app --reload` mean?** Uvicorn imports the module `main` (main.py) and uses the variable `app` inside it as the ASGI application. `--reload` restarts the server when code changes – for development only.

## Homework
Add two endpoints to `main.py`:
1. `GET /contact` → returns your email and website.
2. `GET /stats` (as `async def`) → returns `{"total_courses": 3}`, calculated with `len(COURSES)`.
Test both in `/docs`. Answer at the start of Video 8.

## Homework answer (shown at the start of Video 8)
```python
@app.get("/contact")
def contact() -> dict[str, str]:
    return {"email": "nileshhanumantborate@gmail.com", "website": "https://www.nileshtechnology.in"}


@app.get("/stats")
async def stats() -> dict[str, int]:
    return {"total_courses": len(COURSES)}
```
Full file: [`../08-path-parameters/homework_video7.py`](../08-path-parameters/homework_video7.py)
