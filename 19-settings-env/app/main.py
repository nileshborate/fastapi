# Video 19 - Settings and Environment Variables
# Run (from the 19-settings-env folder):  fastapi dev app/main.py   (copy .env.example to .env first)
from fastapi import Depends, FastAPI

from app.config import get_settings
from app.dependencies import SettingsDep, request_timer
from app.routers import admin, courses, students, teachers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="2.3.0",
    docs_url="/docs" if settings.show_docs else None,       # hide the docs in production
    redoc_url="/redoc" if settings.show_docs else None,
    dependencies=[Depends(request_timer)],                   # homework answer (Video 18): app-wide
)

app.include_router(courses.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def health(settings: SettingsDep) -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
    }
