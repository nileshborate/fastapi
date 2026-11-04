# Video 30 - The Association Object: a link with its own data   (a fresh, small project)
# 1. alembic upgrade head        2. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.database import engine
from app.errors import ConflictError, NotFoundError
from app.routers import courses, students


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # no create_all: Alembic owns the tables (Videos 28-29)
    yield
    engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


app.include_router(students.router)
app.include_router(courses.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
