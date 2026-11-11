from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.roles import Role


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lower_email(cls, email: str) -> str:
        return email.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: Role


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scope: str                          # what the token REALLY got (may be less than asked)


class CourseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    fee: int = Field(ge=0)


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    fee: int
    teacher_id: int
