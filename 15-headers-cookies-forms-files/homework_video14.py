# Homework answer from Video 14 - ShopError + exception handlers
# Run:  fastapi dev homework_video14.py
import logging
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("shop")
app = FastAPI(title="Shop - Homework 14")

PRODUCTS: dict[int, dict[str, Any]] = {
    1: {"id": 1, "name": "FastAPI eBook", "stock": 5},
    2: {"id": 2, "name": "Python Mug", "stock": 0},
}


class ShopError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code


class ProductNotFoundError(ShopError):
    def __init__(self, product_id: int) -> None:
        super().__init__("PRODUCT_NOT_FOUND", f"Product {product_id} not found", status.HTTP_404_NOT_FOUND)


class OutOfStockError(ShopError):
    def __init__(self, product_id: int) -> None:
        super().__init__("OUT_OF_STOCK", f"Product {product_id} is out of stock", status.HTTP_409_CONFLICT)


@app.exception_handler(ShopError)
async def shop_error_handler(request: Request, exc: ShopError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = uuid4().hex                                   # bonus
    logger.exception("Unexpected error, request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Something went wrong.", "request_id": request_id}},
    )


@app.post("/products/{product_id}/buy")
def buy(product_id: int) -> dict[str, Any]:
    product = PRODUCTS.get(product_id)
    if product is None:
        raise ProductNotFoundError(product_id)
    if product["stock"] == 0:
        raise OutOfStockError(product_id)
    product["stock"] -= 1
    return {"product_id": product_id, "stock_left": product["stock"]}
