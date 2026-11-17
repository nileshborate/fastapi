# Version 1 - the shape the OLD apps know. We never change it again.
from pydantic import BaseModel, Field

from app.store import CourseRecord


class CourseV1(BaseModel):
    id: int
    name: str                               # v1 called it "name"
    teacher: str                            # just a string
    price: int                              # whole rupees - 299.50 became 299 (the bug)

    @classmethod
    def from_record(cls, r: CourseRecord) -> "CourseV1":
        return cls(id=r.id, name=r.title, teacher=r.teacher, price=r.price_paise // 100)


class CourseInV1(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    teacher: str = Field(min_length=2, max_length=40)
    price: int = Field(ge=0, le=100_000)
