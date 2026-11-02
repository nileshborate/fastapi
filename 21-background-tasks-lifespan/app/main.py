# Video 21 - Background Tasks and Lifespan Events
# Run (from the 21-background-tasks-lifespan folder):  fastapi dev app/main.py
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
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
    if config.load_seed_data:
        count = course_service.load_courses(config.seed_file)
        print(f"Startup: loaded {count} courses from {config.seed_file}")

    yield                               # the app runs and answers requests here

    # ---------- SHUTDOWN: runs ONCE, when the server stops
    print(f"Shutdown: {len(course_service.COURSES)} courses in memory. Goodbye!")
    course_service.COURSES.clear()


app = FastAPI(
    title=settings.app_name,
    version="2.5.0",
    docs_url="/docs" if settings.show_docs else None,       # hide the docs in production
    redoc_url="/redoc" if settings.show_docs else None,
    lifespan=lifespan,                                       # NEW: startup + shutdown code
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
    }
