# Video 34 - Async Database Part 2: gather, sync vs async measured, blocking code
# 1. alembic upgrade head        2. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import bench, school, stats


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)
app.include_router(school.router)
app.include_router(stats.router)
app.include_router(stats.teachers_router)        # homework (Video 34)
app.include_router(bench.router)


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name, "driver": engine.dialect.driver}
