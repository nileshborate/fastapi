from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)
    teacher_id: int = Field(gt=0)                 # the client sends the ID of the teacher


class TeacherBrief(BaseModel):                    # a teacher INSIDE a course - only what we need
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float
    teacher: TeacherBrief                         # NESTED: read from course.teacher (the relationship)
