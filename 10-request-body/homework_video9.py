# Answer to the Video 9 homework
from enum import Enum
from typing import Annotated, Any

from fastapi import FastAPI, Query

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


class SortBy(Enum):   # plain Enum: a member named "title" would clash with str.title
    title = "title"
    price = "price"


@app.get("/courses")
def list_courses(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    level: Level | None = None,
    max_price: int | None = None,                 # homework 1
    sort_by: SortBy | None = None,                # homework 2
) -> list[dict[str, Any]]:
    result = COURSES
    if level is not None:
        result = [course for course in result if course["level"] == level.value]
    if max_price is not None:
        result = [course for course in result if course["price"] <= max_price]
    if sort_by is not None:
        result = sorted(result, key=lambda course: course[sort_by.value])
    return result[skip : skip + limit]


@app.get("/search")
def search_courses(
    q: Annotated[str, Query(min_length=2, max_length=50)],
    level: Level | None = None,                   # homework 3
) -> list[dict[str, Any]]:
    result = [course for course in COURSES if q.lower() in course["title"].lower()]
    if level is not None:
        result = [course for course in result if course["level"] == level.value]
    return result
