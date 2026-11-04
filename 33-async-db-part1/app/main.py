# Video 33 - Async Database Part 1: async def + AsyncSession + an async driver
# 1. alembic upgrade head        2. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import courses, teachers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()          # async engine: dispose() is awaited too


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)
app.include_router(teachers.router)
app.include_router(courses.router)


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name, "driver": engine.dialect.driver}
