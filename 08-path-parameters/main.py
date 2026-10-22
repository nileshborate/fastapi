# Video 8 - Path Parameters
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from enum import Enum
from typing import Annotated

from fastapi import FastAPI, HTTPException, Path

app = FastAPI(title="Course Hub API", version="1.1.0")

COURSES: list[dict[str, str | int]] = [
    {"id": 1, "title": "FastAPI Basics", "level": "beginner"},
    {"id": 2, "title": "Pydantic Models", "level": "beginner"},
    {"id": 3, "title": "Databases with SQLAlchemy", "level": "intermediate"},
]


class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


@app.get("/courses")
def list_courses() -> list[dict[str, str | int]]:
    return COURSES


# Fixed paths BEFORE paths with parameters (route order matters!)
@app.get("/courses/latest")
def latest_course() -> dict[str, str | int]:
    return COURSES[-1]


# 1. A typed path parameter + validation with Path()
@app.get("/courses/{course_id}")
def get_course(course_id: Annotated[int, Path(gt=0)]) -> dict[str, str | int]:
    for course in COURSES:
        if course["id"] == course_id:
            return course
    raise HTTPException(status_code=404, detail="Course not found")


# 2. Enum path parameter: only fixed values allowed
@app.get("/levels/{level}")
def courses_by_level(level: Level) -> list[dict[str, str | int]]:
    return [course for course in COURSES if course["level"] == level.value]


# 3. Multiple path parameters
@app.get("/students/{student_id}/courses/{course_id}")
def student_course(student_id: int, course_id: int) -> dict[str, int]:
    return {"student_id": student_id, "course_id": course_id}


# 4. A path parameter that can contain slashes
@app.get("/files/{file_path:path}")
def read_file(file_path: str) -> dict[str, str]:
    return {"file_path": file_path}
