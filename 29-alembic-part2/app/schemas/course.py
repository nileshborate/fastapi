from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["beginner", "intermediate", "advanced"]


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    fee: float = Field(ge=0)
    level: Level = "beginner"
    description: str | None = None
    teacher_id: int | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    fee: float
    fee_paise: int
    slug: str
    level: str
    description: str | None
    teacher_id: int | None
