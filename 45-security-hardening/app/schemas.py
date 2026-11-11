# Input limits live HERE: every string has a max_length, every number a range
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)     # Argon2 on 1 MB? no, thanks

    @field_validator("email")
    @classmethod
    def lower_email(cls, email: str) -> str:
        return email.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str                                           # never the password_hash


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CourseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")                # no owner_id from outside

    title: str = Field(min_length=3, max_length=100)
    description: str = Field(default="", max_length=2000)
    fee: int = Field(ge=0, le=100_000)


class CourseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    fee: int | None = Field(default=None, ge=0, le=100_000)


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    fee: int
    owner_id: int
