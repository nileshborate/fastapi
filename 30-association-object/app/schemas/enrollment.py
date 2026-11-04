# The association object in the API: the link's own data + the object on the OTHER side
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.course import CourseOut
from app.schemas.student import StudentOut


class EnrollmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: int


class GradeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade: int = Field(ge=0, le=100)


class EnrollmentOut(BaseModel):              # seen from a student: which course, when, which grade
    model_config = ConfigDict(from_attributes=True)

    course: CourseOut
    enrolled_at: datetime
    grade: int | None


class RosterRow(BaseModel):                  # seen from a course: which student, when, which grade
    model_config = ConfigDict(from_attributes=True)

    student: StudentOut
    enrolled_at: datetime
    grade: int | None


class StudentDetail(StudentOut):
    enrollments: list[EnrollmentOut]


class CourseDetail(CourseOut):
    enrollments: list[RosterRow]
