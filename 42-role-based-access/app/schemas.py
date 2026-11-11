from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.roles import Role


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")        # {"role": "admin"} -> 422

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
    is_active: bool


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Role                                       # only admin, teacher or student


class ActiveUpdate(BaseModel):
    """homework 42: PATCH /admin/users/{id}/active"""
    model_config = ConfigDict(extra="forbid")

    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CourseIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=200)
    fee: int = Field(ge=0)


class CourseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    fee: int | None = Field(default=None, ge=0)


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    fee: int
    teacher_id: int
