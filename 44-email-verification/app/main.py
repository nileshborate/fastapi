# Video 44 - Email verification and password reset: one-time links, no user enumeration
# 1. alembic upgrade head        2. fastapi dev app/main.py   (emails are printed)
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="Course Hub API", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
