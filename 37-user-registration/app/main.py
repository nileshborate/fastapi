# Video 37 - User Registration and Password Hashing (Argon2 with pwdlib)
# 1. alembic upgrade head        2. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import engine
from app.errors import AuthError, DomainError
from app.routers import users


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="Users API", version="1.0.0", lifespan=lifespan)
app.include_router(users.router)


@app.exception_handler(DomainError)
async def domain_error(request: Request, exc: DomainError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, AuthError) else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message},
                        headers=headers)


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "database": engine.dialect.name}
