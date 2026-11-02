# Router-level dependencies: they run for EVERY endpoint in this router
from fastapi import APIRouter, Depends
from sqlalchemy import inspect

from app.database import engine
from app.dependencies import CurrentRole, DBSession, SettingsDep, audit_log, require_admin, verify_api_key
from app.services import course_service, student_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_api_key), Depends(require_admin), Depends(audit_log)],
)


@router.get("/stats")
def stats(db: DBSession, role: CurrentRole) -> dict[str, int | str]:
    courses = course_service.count_courses(db)                   # counted in the DATABASE
    students = student_service.count_students(db)                # homework answer (Video 23)
    return {"courses": courses, "students": students, "checked_by": role}


@router.get("/db")                                              # homework answer (Video 23)
def database_info() -> dict[str, str | list[str]]:
    return {"database": engine.dialect.name, "tables": sorted(inspect(engine).get_table_names())}


@router.get("/config")                                          # homework answer (Video 19)
def config(settings: SettingsDep) -> dict[str, str | bool | int]:
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
        "max_upload_mb": settings.max_upload_mb,
    }                                                           # never the API key!
