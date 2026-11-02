from pydantic import BaseModel, Field


class TeacherCreate(BaseModel):
    name: str = Field(min_length=2)
    subject: str = Field(min_length=2)


class TeacherOut(BaseModel):
    id: int
    name: str
    subject: str
