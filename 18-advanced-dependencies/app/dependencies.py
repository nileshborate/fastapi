# Dependencies = small reusable functions (or classes). FastAPI calls them for us with Depends().
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status

from app.schemas.course import CourseOut
from app.schemas.student import StudentOut
from app.services import course_service, student_service

API_KEY = "learn-fastapi-123"      # demo only - secrets move to settings in a later video


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


# ---------------------------------------------------------------- 2. checks + loaders (Video 17)
def verify_api_key(x_api_key: Annotated[str, Header()]) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def get_course_or_404(course_id: int) -> CourseOut:
    course = course_service.get_course(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


def get_student_or_404(student_id: int) -> StudentOut:          # homework answer (Video 17)
    student = student_service.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


CourseDep = Annotated[CourseOut, Depends(get_course_or_404)]
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


# ---------------------------------------------------------------- 5. yield: setup + cleanup
EVENTS: list[str] = []               # so tests (and you) can see what happened


class FakeSession:
    """Stands in for a real database session - the database videos use the same pattern."""

    def __init__(self) -> None:
        EVENTS.append("session opened")
        print("session opened")

    def count(self, table: str) -> int:
        if table == "courses":
            return len(course_service.COURSES)
        return len(student_service.STUDENTS)

    def close(self) -> None:
        EVENTS.append("session closed")
        print("session closed")


def get_db() -> Iterator[FakeSession]:
    db = FakeSession()          # 1. setup  - before the endpoint
    try:
        yield db                # 2. the endpoint runs here
    finally:
        db.close()              # 3. cleanup - after the endpoint, even after an error


DBSession = Annotated[FakeSession, Depends(get_db)]
