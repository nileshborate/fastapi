from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    role: str


# ---------------------------------------------------------------- homework answer (Video 36)
class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)       # shorter -> 422
