from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)
    max_students: int = Field(default=30, ge=1)         # homework answer (Video 27)


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    price: float
    max_students: int                                   # homework answer (Video 27)
    student_count: int
