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


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    fee: int
    teacher: TeacherOut


class Stats(BaseModel):         # NEW: four numbers from four queries - at the same time
    teachers: int
    courses: int
    average_fee: float
    top_courses: list[str]


# ---------------------------------------------------------------- homework answer (Video 34)
class TeacherSummary(BaseModel):
    id: int
    name: str
    courses: int
    total_fees: int
