# Homework answer (Video 31): the students list - filters, pagination, a count per student
from pydantic import BaseModel, ConfigDict, Field


class StudentFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    city: str | None = Field(default=None, max_length=50)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)


class StudentRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
    courses: int                    # how many courses - a count per student


class TopStudent(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    average_grade: float
