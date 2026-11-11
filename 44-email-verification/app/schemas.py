from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
    is_verified: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class LinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=20, max_length=100)


class ResetIn(LinkIn):
    new_password: str = Field(min_length=8, max_length=128)


class PasswordChange(BaseModel):
    """homework 44: POST /me/password"""
    model_config = ConfigDict(extra="forbid")

    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class Message(BaseModel):
    detail: str
