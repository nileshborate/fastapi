from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StudentBase(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr


class StudentCreate(StudentBase):
    model_config = ConfigDict(extra="forbid")


class StudentUpdate(BaseModel):                  # homework answer (Video 25): PATCH
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None

    @field_validator("name", "email")
    @classmethod
    def not_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("may be left out, but not null")
        return value


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
