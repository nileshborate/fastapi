# Video 55 - structured logging: JSON lines, a request id on every line, errors with context
# fastapi dev app/main.py      ·      LOG_JSON=false fastapi dev app/main.py
import logging

from fastapi import FastAPI, Response
from pydantic import BaseModel, EmailStr

from app import services
from app.logging_setup import setup_logging
from app.middleware import RequestContextMiddleware

setup_logging()
log = logging.getLogger("app")

app = FastAPI(title="Course Hub - structured logging")
app.add_middleware(RequestContextMiddleware)


class EnrollIn(BaseModel):
    email: EmailStr
    course_id: int
    card_number: str


@app.post("/enrollments", status_code=201)
def create_enrollment(data: EnrollIn, response: Response) -> dict[str, object]:
    result = services.enroll(data.email, data.course_id, data.card_number)
    if not result["new"]:
        response.status_code = 200          # already enrolled - nothing was created
    return result


@app.get("/reports/{course_id}")
async def report(course_id: int) -> dict[str, object]:
    return await services.build_report(course_id)


@app.get("/boom")
def boom() -> dict[str, float]:
    students = 0
    return {"average": 100 / students}          # ZeroDivisionError - a real bug
