# Version 2 - the BREAKING changes: a renamed field, a price object, a teacher object
from decimal import Decimal

from pydantic import BaseModel, Field

from app.store import CourseRecord

CENTS = Decimal("0.01")


class Money(BaseModel):
    amount: Decimal = Field(ge=0, le=100_000, decimal_places=2)   # "299.50" - exact
    currency: str = Field(default="INR", pattern=r"^[A-Z]{3}$")


class Teacher(BaseModel):
    name: str


class CourseV2(BaseModel):
    id: int
    title: str                              # renamed: name -> title
    teacher: Teacher                        # str -> object (room for more later)
    price: Money                            # int -> {amount, currency}
    tags: list[str]                         # new

    @classmethod
    def from_record(cls, r: CourseRecord) -> "CourseV2":
        return cls(id=r.id, title=r.title, teacher=Teacher(name=r.teacher),
                   price=Money(amount=(Decimal(r.price_paise) / 100).quantize(CENTS),
                                 currency=r.currency),
                   tags=r.tags)


class CourseInV2(BaseModel):
    title: str = Field(min_length=2, max_length=80)
    teacher: Teacher
    price: Money
    tags: list[str] = Field(default=[], max_length=5)
