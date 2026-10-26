# Video 14 - Error Handling the Right Way
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
import logging
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("coursehub")
app = FastAPI(title="Course Hub API", version="1.7.0")

COURSES: dict[int, dict[str, Any]] = {
    1: {"id": 1, "title": "FastAPI Basics", "seats": 2, "students": []},
    2: {"id": 2, "title": "Pydantic Models", "seats": 0, "students": []},
}


# ---------------------------------------------------------------- 1. custom exceptions
class CourseHubError(Exception):
    """Base class for all expected business errors in our app."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code


class CourseFullError(CourseHubError):
    def __init__(self, course_id: int) -> None:
        super().__init__("COURSE_FULL", f"Course {course_id} has no free seats", status.HTTP_409_CONFLICT)


class AlreadyEnrolledError(CourseHubError):
    def __init__(self, student: str) -> None:
        super().__init__("ALREADY_ENROLLED", f"{student} is already enrolled", status.HTTP_409_CONFLICT)


# ---------------------------------------------------------------- 2. exception handlers
def error_body(code: str, message: str, **extra: Any) -> dict[str, Any]:
    """ONE error format for the whole API."""
    return {"error": {"code": code, "message": message, **extra}}


@app.exception_handler(CourseHubError)
async def coursehub_error_handler(request: Request, exc: CourseHubError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_body(exc.code, exc.message, path=request.url.path))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [{"field": ".".join(str(part) for part in err["loc"][1:]), "message": err["msg"]} for err in exc.errors()]
    return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", "Invalid request", details=details))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": f"HTTP_{exc.status_code}", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected error on %s", request.url.path)   # full details go to the LOG only
    return JSONResponse(status_code=500, content=error_body("INTERNAL_ERROR", "Something went wrong. Please try again."))


# ---------------------------------------------------------------- 3. endpoints
class Enrollment(BaseModel):
    student: str = Field(min_length=2)


@app.get("/courses/{course_id}")
def get_course(course_id: Annotated[int, Path(gt=0)]) -> dict[str, Any]:
    if course_id not in COURSES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
            headers={"X-Error-Code": "COURSE_NOT_FOUND"},
        )
    return COURSES[course_id]


@app.delete("/courses/{course_id}")
def delete_course(course_id: Annotated[int, Path(gt=0)]) -> None:
    # detail can be a dict with your own fields
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "NOT_ALLOWED", "message": "Only admins can delete courses", "required_role": "admin"},
    )


@app.post("/courses/{course_id}/enroll", status_code=status.HTTP_201_CREATED)
def enroll(course_id: Annotated[int, Path(gt=0)], enrollment: Enrollment) -> dict[str, Any]:
    course = COURSES.get(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    if enrollment.student in course["students"]:
        raise AlreadyEnrolledError(enrollment.student)
    if len(course["students"]) >= course["seats"]:
        raise CourseFullError(course_id)
    course["students"].append(enrollment.student)
    return {"course_id": course_id, "student": enrollment.student, "seats_left": course["seats"] - len(course["students"])}


@app.get("/crash")
def crash() -> dict[str, Any]:
    # a bug on purpose: dividing by zero
    return {"result": 1 / 0}
