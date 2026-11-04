from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Level = Literal["beginner", "intermediate", "advanced"]


class CourseFilters(BaseModel):     # the query parameters - as ONE model (Video 25)
    model_config = ConfigDict(extra="forbid")

    q: str | None = Field(default=None, max_length=50)     # part of the title
    level: Level | None = None
    teacher: str | None = Field(default=None, max_length=50)   # a column of ANOTHER table
    max_fee: float | None = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class CourseRow(BaseModel):         # exactly the columns we SELECT - not the whole model
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    level: str
    fee: float
    teacher: str                    # Teacher.name, labelled "teacher"
