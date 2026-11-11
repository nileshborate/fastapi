# Video 45 - API security hardening: rate limits, input limits, headers, HTTPS, safe errors
# 1. alembic upgrade head        2. fastapi dev app/main.py
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import Settings, get_settings
from app.database import engine
from app.middleware import BodySizeLimit, SecurityHeaders
from app.ratelimit import RateLimiter
from app.routers import auth, courses

log = logging.getLogger("coursehub")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


def create_app(settings: Settings) -> FastAPI:
    prod = settings.is_production
    app = FastAPI(title="Course Hub API", version="1.0.0", lifespan=lifespan,
                  docs_url=None if prod else "/docs",              # no map for attackers
                  redoc_url=None if prod else "/redoc",
                  openapi_url=None if prod else "/openapi.json")
    app.state.login_limiter = RateLimiter(settings.login_limit, settings.login_window_seconds)
    app.state.write_limiter = RateLimiter(10, 60)                  # 10 writes / minute
    app.state.ip_limiter = RateLimiter(20, 60)                     # 20 / minute / IP
    app.state.domain_limiter = RateLimiter(settings.domain_limit,  # homework 45
                                           settings.domain_window_seconds)

    # the LAST one added runs FIRST - so this list goes from the inside to the outside
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["GET", "POST", "PATCH"],
                       allow_headers=["Authorization", "Content-Type"])
    app.add_middleware(BodySizeLimit, max_bytes=settings.max_body_bytes)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
    if prod:
        app.add_middleware(HTTPSRedirectMiddleware)                # http:// -> https://
    app.add_middleware(SecurityHeaders, hsts=prod)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        error_id = uuid.uuid4().hex[:8]                            # to find it in the log
        log.exception("error %s on %s %s", error_id, request.method, request.url.path)
        return JSONResponse(status_code=500,
                            content={"detail": "Internal server error", "error_id": error_id})

    app.include_router(auth.router)
    app.include_router(courses.router)

    @app.get("/", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app(get_settings())
