# Video 43 - OAuth2 scopes: Security(), SecurityScopes, scopes in the token
# 1. alembic upgrade head   2. python -m app.make_admin <email>   3. fastapi dev app/main.py
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import engine
from app.routers import admin, auth, courses


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(title="Course Hub API", version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
