# Report rows: each one is a SELECT result with labelled columns - not a model
from pydantic import BaseModel, ConfigDict


class CourseStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    teacher: str
    students: int
    average_grade: float | None     # no grades yet -> NULL


class TeacherStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    teacher: str
    courses: int
    students: int                   # DIFFERENT students


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    city: str
