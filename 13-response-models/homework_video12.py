# Answer to the Video 12 homework: OrderCreate with nested items, coupon validator and a model validator
from typing import Any, Self

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

app = FastAPI(title="Course Hub API", version="1.5.0")


class OrderItem(BaseModel):
    course_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1, le=10)


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OrderItem] = Field(min_length=1)
    coupon: str | None = None

    @field_validator("coupon")
    @classmethod
    def clean_coupon(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().upper()
        if not value.isalnum():
            raise ValueError("coupon may contain only letters and digits")
        return value

    @model_validator(mode="after")
    def free_coupon_one_item(self) -> Self:
        if self.coupon == "FREE100" and len(self.items) > 1:
            raise ValueError("coupon FREE100 allows only 1 item")
        return self


@app.post("/orders", status_code=201)
def create_order(order: OrderCreate) -> dict[str, Any]:
    return order.model_dump()
