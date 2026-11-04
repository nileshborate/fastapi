# Video 28 - Alembic Part 1: why migrations + the first migration   (a fresh, small project)
# 1. alembic upgrade head        2. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import courses


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # NO Base.metadata.create_all() any more: Alembic owns the tables now
    yield
    engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)
app.include_router(courses.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
