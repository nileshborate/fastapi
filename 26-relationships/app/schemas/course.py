from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)
    teacher_id: int = Field(gt=0)                 # the client sends the ID of the teacher


class CourseUpdate(BaseModel):                    # homework answer (Video 26): PATCH
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=100)
    price: float | None = Field(default=None, ge=0)
    teacher_id: int | None = Field(default=None, gt=0)     # move the course to another teacher

    @field_validator("title", "price", "teacher_id")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("may be left out, but not null")
        return value


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
