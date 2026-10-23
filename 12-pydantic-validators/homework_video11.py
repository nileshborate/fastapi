# Answer to the Video 11 homework: CourseCreate with Field()
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Course Hub API", version="1.4.0")


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100, examples=["FastAPI Basics"])
    price: int = Field(default=0, ge=0, le=50000, description="Price in rupees")
    level: str = Field(default="beginner", pattern=r"^(beginner|intermediate|advanced)$")
    tags: list[str] = Field(default_factory=list, max_length=5)


@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    return course.model_dump()
