from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

COMMON_PASSWORDS = {"password", "password123", "12345678", "123456789", "qwerty123",
                    "iloveyou", "admin123", "welcome123", "letmein123", "11111111"}


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr                                     # a real email format, or 422
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def lower_email(cls, email: str) -> str:
        return email.strip().lower()                    # Asha@X.com = asha@x.com

    @model_validator(mode="after")
    def strong_enough(self) -> "UserCreate":
        if self.password.lower() in COMMON_PASSWORDS:
            raise ValueError("This password is too common")
        if self.email.split("@")[0] in self.password.lower():
            raise ValueError("The password must not contain your email name")
        return self


class UserOut(BaseModel):                               # NO password, NO hash
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class LoginCheck(BaseModel):
    email: EmailStr
    password: str
