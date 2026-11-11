# What clients may send - WebSocket messages are input too (Video 45: limits everywhere)
from pydantic import BaseModel, ConfigDict, Field


class ChatIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    to: str | None = Field(default=None, max_length=20)   # homework 46: a private message


class Announcement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=200)


class Delivered(BaseModel):
    delivered_to: int
