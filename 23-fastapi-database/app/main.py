# Video 23 - Connecting FastAPI to a Database
# Run (from the 23-fastapi-database folder):  fastapi dev app/main.py
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app import models  # noqa: F401  - imports every model, so Base knows all the tables
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.dependencies import SettingsDep
from app.middleware import limit_upload_size, request_id_and_timing, security_headers
from app.routers import admin, courses, students, teachers
from app.services import course_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ---------- STARTUP: runs ONCE, before the first request
    config = get_settings()
    app.state.started_at = time.time()
    Base.metadata.create_all(bind=engine)          # NEW: CREATE TABLE for every model - if missing
    print(f"Database: {engine.url.render_as_string(hide_password=True)}")
    if config.load_seed_data:
        if config.seed_file.exists():
            with SessionLocal() as db:             # a session OUTSIDE a request: we open it ourselves
                count = course_service.load_courses(db, config.seed_file)
            print(f"Startup: loaded {count} courses from {config.seed_file}" if count else
                  "Startup: the database already has courses - nothing loaded")
        else:
            print(f"Warning: {config.seed_file} not found - starting with empty data")

    yield                               # the app runs and answers requests here

    # ---------- SHUTDOWN: runs ONCE, when the server stops
    engine.dispose()                    # NEW: close all database connections
    print("Shutdown: database connections closed. Goodbye!")


app = FastAPI(
    title=settings.app_name,
    version="2.6.0",
    docs_url="/docs" if settings.show_docs else None,       # hide the docs in production
    redoc_url="/redoc" if settings.show_docs else None,
    lifespan=lifespan,                                       # startup + shutdown (Video 21)
)

# -------------------------------------------- middleware (the LAST one added runs FIRST)
app.middleware("http")(limit_upload_size)                   # homework: 413 for big requests
app.middleware("http")(security_headers)                    # homework: 3 security headers
app.middleware("http")(request_id_and_timing)               # request id + timing
app.add_middleware(GZipMiddleware, minimum_size=1000)       # compress big responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,                 # who may call us from a browser
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "X-Role", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],      # JavaScript may read these
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)  # homework

app.include_router(courses.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def health(settings: SettingsDep, request: Request) -> dict[str, str | float]:
    uptime = time.time() - request.app.state.started_at      # set by the lifespan
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "request_id": request.state.request_id,
        "uptime_seconds": round(uptime, 1),
        "database": engine.dialect.name,                     # NEW: sqlite or postgresql
    }
