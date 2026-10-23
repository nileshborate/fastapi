# Video 12 - Pydantic Part 2: validators, nested models and model_config
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from datetime import date
from typing import Any, Self

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

app = FastAPI(title="Course Hub API", version="1.5.0")


# 1. Small models that we NEST inside the course
class Instructor(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr


class Lesson(BaseModel):
    title: str = Field(min_length=3)
    minutes: int = Field(gt=0, le=180)


class CourseCreate(BaseModel):
    # 2. model_config: settings for the whole model
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    price: int = Field(default=0, ge=0)
    discount_price: int | None = None
    start_date: date
    end_date: date
    tags: list[str] = Field(default_factory=list)
    instructor: Instructor                                              # nested model
    lessons: list[Lesson] = Field(default_factory=list, max_length=20)  # list of models

    # 3. field_validator: a custom rule for ONE field
    @field_validator("title")
    @classmethod
    def title_not_all_caps(cls, value: str) -> str:
        if value.isupper():
            raise ValueError("title must not be ALL CAPS")
        return value

    # 4. mode="before": runs BEFORE type checking -> accept "python, fastapi" as well as a list
    @field_validator("tags", mode="before")
    @classmethod
    def split_tags(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.split(",")
        return value

    # 5. a validator can also CLEAN the value: lower case, no spaces, no duplicates
    @field_validator("tags")
    @classmethod
    def clean_tags(cls, tags: list[str]) -> list[str]:
        return sorted({tag.strip().lower() for tag in tags if tag.strip()})

    # 6. model_validator: rules that need SEVERAL fields
    @model_validator(mode="after")
    def check_dates_and_price(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if self.discount_price is not None and self.discount_price >= self.price:
            raise ValueError("discount_price must be lower than price")
        return self


@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    data = course.model_dump()
    data["total_minutes"] = sum(lesson.minutes for lesson in course.lessons)
    return data
