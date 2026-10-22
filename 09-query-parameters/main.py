# Video 9 - Query Parameters
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from enum import Enum
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path, Query

app = FastAPI(title="Course Hub API", version="1.2.0")

COURSES: list[dict[str, Any]] = [
    {"id": 1, "title": "FastAPI Basics", "level": "beginner", "price": 0, "published": True},
    {"id": 2, "title": "Pydantic Models", "level": "beginner", "price": 499, "published": True},
    {"id": 3, "title": "Databases with SQLAlchemy", "level": "intermediate", "price": 999, "published": True},
    {"id": 4, "title": "Async Python", "level": "intermediate", "price": 799, "published": False},
    {"id": 5, "title": "Deploying FastAPI", "level": "advanced", "price": 1299, "published": True},
]


class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


# 1. Pagination + optional filters (all query parameters have defaults)
@app.get("/courses")
def list_courses(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    level: Level | None = None,
    published: bool | None = None,
) -> list[dict[str, Any]]:
    result = COURSES
    if level is not None:
        result = [course for course in result if course["level"] == level.value]
    if published is not None:
        result = [course for course in result if course["published"] == published]
    return result[skip : skip + limit]


# 2. A REQUIRED query parameter with length rules
@app.get("/search")
def search_courses(
    q: Annotated[str, Query(min_length=2, max_length=50)],
) -> list[dict[str, Any]]:
    return [course for course in COURSES if q.lower() in course["title"].lower()]


# 3. Multiple values for one parameter:  /courses/by-ids?ids=1&ids=3
@app.get("/courses/by-ids")
def courses_by_ids(ids: Annotated[list[int], Query()]) -> list[dict[str, Any]]:
    return [course for course in COURSES if course["id"] in ids]


# 4. Path parameter + query parameter together
@app.get("/courses/{course_id}")
def get_course(
    course_id: Annotated[int, Path(gt=0)],
    include_price: bool = False,
) -> dict[str, Any]:
    for course in COURSES:
        if course["id"] == course_id:
            if include_price:
                return course
            return {key: value for key, value in course.items() if key != "price"}
    raise HTTPException(status_code=404, detail="Course not found")
