# Video 38 - JWT Explained: header, payload, signature, claims, expiry - with PyJWT
# fastapi dev app/main.py      (no database today)
from fastapi import FastAPI

from app.routers import auth

app = FastAPI(title="JWT Explained", version="1.0.0")
app.include_router(auth.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
