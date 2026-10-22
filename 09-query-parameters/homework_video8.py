# Answer to the Video 8 homework
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


# 1 + 3: only the title, course_id from 1 to 1000
@app.get("/courses/{course_id}/title")
def course_title(course_id: Annotated[int, Path(ge=1, le=1000)]) -> dict[str, str | int]:
    for course in COURSES:
        if course["id"] == course_id:
            return {"title": course["title"]}
    raise HTTPException(status_code=404, detail="Course not found")


# 2: count courses for one level
@app.get("/levels/{level}/count")
def level_count(level: Level) -> dict[str, str | int]:
    count = len([course for course in COURSES if course["level"] == level.value])
    return {"level": level.value, "count": count}
