# Video 26 - Relationships: one teacher, many courses   (a FRESH, small project)
# Run (from the 26-relationships folder):  fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app import models  # noqa: F401  - imports every model, so Base knows all the tables
from app.database import Base, engine
from app.errors import ConflictError, NotFoundError
from app.routers import courses, teachers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)             # CREATE TABLE teachers, courses - if missing
    yield
    engine.dispose()


app = FastAPI(title="School API", version="1.0.0", lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


app.include_router(teachers.router)
app.include_router(courses.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
