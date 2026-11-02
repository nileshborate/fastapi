from pydantic import BaseModel, ConfigDict, Field


class TeacherCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=50)
    subject: str = Field(min_length=2, max_length=50)


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subject: str


class CourseBrief(BaseModel):                     # a course INSIDE a teacher - no teacher again
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float


class TeacherDetail(TeacherOut):                  # one teacher + the list of courses
    courses: list[CourseBrief]
