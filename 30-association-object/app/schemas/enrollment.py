# The association object in the API: the link's own data + the object on the OTHER side
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.course import CourseOut
from app.schemas.student import StudentOut

Status = Literal["active", "completed", "dropped"]          # homework (Video 30)


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: int


class EnrollmentUpdate(BaseModel):          # homework (Video 30): grade AND/OR status
    model_config = ConfigDict(extra="forbid")

    grade: int | None = Field(default=None, ge=0, le=100)
    status: Status | None = None


class EnrollmentOut(BaseModel):              # seen from a student: which course, when, which grade
    model_config = ConfigDict(from_attributes=True)

    course: CourseOut
    enrolled_at: datetime
    grade: int | None
    status: str


class RosterRow(BaseModel):                  # seen from a course: which student, when, which grade
    model_config = ConfigDict(from_attributes=True)

    student: StudentOut
    enrolled_at: datetime
    grade: int | None
    status: str


class StudentDetail(StudentOut):
    enrollments: list[EnrollmentOut]


class CourseDetail(CourseOut):
    enrollments: list[RosterRow]
