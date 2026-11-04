# Video 32 - Transactions and Concurrency: all or nothing, and two requests on one row
# 1. alembic upgrade head    2. fastapi dev app/main.py    3. python -m demos.lost_update
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import engine
from app.errors import ConflictError, NotFoundError
from app.routers import school


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield                           # no create_all: Alembic owns the tables
    engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


app.include_router(school.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
