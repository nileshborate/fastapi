# Schemas = the SHAPE of the data that goes in and out of the API
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseBase(BaseModel):                     # the fields the client SENDS and SEES
    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)


class CourseCreate(CourseBase):                  # INPUT for POST - and for PUT (the FULL course)
    model_config = ConfigDict(extra="forbid")    # an unknown field (like "id") -> 422


class CourseUpdate(BaseModel):                   # NEW: INPUT for PATCH - every field is optional
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=100)
    price: float | None = Field(default=None, ge=0)

    @field_validator("title", "price")
    @classmethod
    def not_null(cls, value: object) -> object:  # you may LEAVE OUT a field, but not send null
        if value is None:
            raise ValueError("may be left out, but not null")
        return value


class CourseOut(CourseBase):                     # OUTPUT: + what the DATABASE creates
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime | None                  # NEW: None until the first update
