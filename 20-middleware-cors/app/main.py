# Video 20 - Middleware and CORS
# Run (from the 20-middleware-cors folder):  fastapi dev app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.config import get_settings
from app.dependencies import SettingsDep
from app.middleware import request_id_and_timing
from app.routers import admin, courses, students, teachers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="2.4.0",
    docs_url="/docs" if settings.show_docs else None,       # hide the docs in production
    redoc_url="/redoc" if settings.show_docs else None,
)

# -------------------------------------------- middleware (the LAST one added runs FIRST)
app.middleware("http")(request_id_and_timing)               # our own: request id + timing
app.add_middleware(GZipMiddleware, minimum_size=1000)       # compress big responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,                 # who may call us from a browser
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "X-Role", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Process-Time"],      # JavaScript may read these
)

app.include_router(courses.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def health(settings: SettingsDep, request: Request) -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "request_id": request.state.request_id,
    }
