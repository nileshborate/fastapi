from pydantic import BaseModel, ConfigDict, Field


class TeacherCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=50)


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    fee: int = Field(ge=0)
    teacher_id: int


class CourseTransfer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    teacher_id: int


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    fee: int
    teacher: TeacherOut


# ---------------------------------------------------------------- homework answer (Video 35)
class FeeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fee: int = Field(ge=0)
