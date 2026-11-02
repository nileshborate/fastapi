# Router-level dependencies: they run for EVERY endpoint in this router
from fastapi import APIRouter, Depends

from app.dependencies import CurrentRole, DBSession, SettingsDep, audit_log, require_admin, verify_api_key
from app.services import course_service, student_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_api_key), Depends(require_admin), Depends(audit_log)],
)


@router.get("/stats")
def stats(db: DBSession, role: CurrentRole) -> dict[str, int | str]:
    courses = course_service.count_courses(db)                   # Video 23: counted in the DATABASE
    return {"courses": courses, "students": len(student_service.STUDENTS), "checked_by": role}


@router.get("/config")                                          # homework answer (Video 19)
def config(settings: SettingsDep) -> dict[str, str | bool | int]:
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "debug": settings.debug,
        "max_upload_mb": settings.max_upload_mb,
    }                                                           # never the API key!
