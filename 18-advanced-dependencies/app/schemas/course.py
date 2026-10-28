# Schemas = the SHAPE of the data that goes in and out of the API
from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    price: float = Field(ge=0)


class CourseOut(BaseModel):
    id: int
    title: str
    price: float
