# Video 36 - Security Fundamentals: authentication vs authorization, sessions vs tokens
# fastapi dev app/main.py      (no database today - the users live in app/users.py)
from fastapi import FastAPI

from app.routers import session_auth, token_auth

app = FastAPI(title="Security Fundamentals", version="1.0.0")
app.include_router(session_auth.router)
app.include_router(token_auth.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
