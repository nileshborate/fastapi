from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TeacherBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr                                      # homework answer (Video 24)
    subject: str = Field(min_length=2, max_length=50)


class TeacherCreate(TeacherBase):
    model_config = ConfigDict(extra="forbid")


class TeacherOut(TeacherBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
