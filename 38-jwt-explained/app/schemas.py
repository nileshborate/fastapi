from pydantic import BaseModel


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int                 # seconds - the client knows when to get a new one


class MeOut(BaseModel):
    id: int
    email: str
    name: str                       # homework (Video 38): from the token
    role: str
    token_expires: int              # the exp claim
