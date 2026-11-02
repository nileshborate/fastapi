# Schemas = the SHAPE of the data that goes in and out of the API
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseBase(BaseModel):                     # the fields the client SENDS and SEES
    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)


class CourseCreate(CourseBase):                  # INPUT: only what the client may send
    model_config = ConfigDict(extra="forbid")    # an unknown field (like "id") -> 422


class CourseOut(CourseBase):                     # OUTPUT: + what the DATABASE creates
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
