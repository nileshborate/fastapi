# Dependencies = small reusable functions (or classes). FastAPI calls them for us with Depends().
import secrets
from typing import Annotated

from fastapi import BackgroundTasks, Depends, Header, HTTPException, Query, Request, status

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Course
from app.schemas.student import StudentOut
from app.services import course_service, student_service
from app.tasks import write_log

SettingsDep = Annotated[Settings, Depends(get_settings)]
DBSession = Annotated[Session, Depends(get_db)]            # NEW (Video 23): a real database session


# ---------------------------------------------------------------- 1. a CLASS as a dependency
class PaginationParams:
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
    ) -> None:
        self.skip = skip
        self.limit = limit


Pagination = Annotated[PaginationParams, Depends()]     # Depends() with no argument = use the type


class CourseFilter:                                         # homework answer (Video 18)
    def __init__(
        self,
        min_price: Annotated[float | None, Query(ge=0)] = None,
        max_price: Annotated[float | None, Query(ge=0)] = None,
    ) -> None:
        self.min_price = min_price
        self.max_price = max_price


Filters = Annotated[CourseFilter, Depends()]


# ---------------------------------------------------------------- 2. checks + loaders (Video 17)
def verify_api_key(x_api_key: Annotated[str, Header()], settings: SettingsDep) -> None:
    expected = settings.api_key.get_secret_value()
    if not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def get_course_or_404(course_id: int, db: DBSession) -> Course:
    course = course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def get_student_or_404(student_id: int) -> StudentOut:          # homework answer (Video 17)
    student = student_service.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


CourseDep = Annotated[Course, Depends(get_course_or_404)]
StudentDep = Annotated[StudentOut, Depends(get_student_or_404)]


# ---------------------------------------------------------------- 3. sub-dependencies
def get_role(x_role: Annotated[str, Header()] = "student") -> str:
    return x_role.lower()


CurrentRole = Annotated[str, Depends(get_role)]


def require_admin(role: CurrentRole) -> None:                    # depends on get_role
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")


# ---------------------------------------------------------------- 4. a class with settings
class RoleChecker:
    def __init__(self, allowed_roles: list[str]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, role: CurrentRole) -> str:
        if role not in self.allowed_roles:
            detail = f"Allowed roles: {self.allowed_roles}"
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return role


allow_staff = RoleChecker(["admin", "teacher"])
allow_teachers = RoleChecker(["admin", "teacher"])          # homework answer (Video 18)


# ---------------------------------------------------------------- 5. background tasks in a dependency
def audit_log(request: Request, background_tasks: BackgroundTasks, settings: SettingsDep) -> None:
    message = f"audit: {request.method} {request.url.path}"
    background_tasks.add_task(write_log, message, settings.log_file)      # the SAME task list
