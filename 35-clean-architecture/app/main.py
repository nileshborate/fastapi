# Video 35 - Clean Architecture: router -> service -> repository (+ unit of work)
# 1. alembic upgrade head        2. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import engine
from app.errors import DomainError
from app.routers import courses, teachers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)
app.include_router(teachers.router)
app.include_router(courses.router)


@app.exception_handler(DomainError)
async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
    # ONE place turns business errors into HTTP answers
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
