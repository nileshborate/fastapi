from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr


class StudentCreate(StudentBase):
    model_config = ConfigDict(extra="forbid")


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
