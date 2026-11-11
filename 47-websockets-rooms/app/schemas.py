from pydantic import BaseModel, ConfigDict, Field


class ChatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)


class Announcement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=200)


class Delivered(BaseModel):
    room: str
    delivered_to: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
