# Video 40 - Protected routes: get_current_user, 401 vs 403, the owner check
# 1. alembic upgrade head        2. fastapi dev app/main.py   ->  /docs  ->  Authorize
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import auth, courses, me


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="Course Hub API", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(courses.router)


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
