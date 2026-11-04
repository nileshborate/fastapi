# Video 31 - Advanced Queries: joins, group by, having, exists, pagination with totals
# 1. alembic upgrade head    2. python -m app.seed    3. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import courses, reports


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield                           # no create_all: Alembic owns the tables
    engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)
app.include_router(courses.router)
app.include_router(reports.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
