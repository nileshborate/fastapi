# Video 11 - Pydantic Field(): rules, email, defaults and examples
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Course Hub API", version="1.4.0")


class StudentCreate(BaseModel):
    # text rules + an example for the docs
    name: str = Field(min_length=2, max_length=50, examples=["Asha Patil"])
    # EmailStr checks the email format (needs email-validator, included in fastapi[standard])
    email: EmailStr = Field(examples=["asha@example.com"])
    # number rules; strict=True means "20" (text) is NOT converted to 20
    age: int | None = Field(default=None, ge=10, le=100, strict=True)
    # regular expression: a 10-digit Indian mobile number starting with 6-9
    phone: str | None = Field(
        default=None,
        pattern=r"^[6-9]\d{9}$",
        description="10-digit mobile number",
        examples=["9876543210"],
    )
    # a fresh empty list for every student, at most 5 course ids
    courses: list[int] = Field(default_factory=list, max_length=5)


# The same rules can also be written with Annotated (like Path and Query)
CourseTitle = Annotated[str, Field(min_length=3, max_length=100)]


class CourseCreate(BaseModel):
    title: CourseTitle
    price: int = Field(default=0, ge=0, description="Price in rupees")


STUDENTS: list[dict[str, Any]] = []


def next_id() -> int:
    return max((student["id"] for student in STUDENTS), default=0) + 1


@app.get("/students")
def list_students() -> list[dict[str, Any]]:
    return STUDENTS


@app.post("/students", status_code=201)
def create_student(student: StudentCreate) -> dict[str, Any]:
    new_student = {"id": next_id(), **student.model_dump()}
    STUDENTS.append(new_student)
    return new_student


@app.put("/students/{student_id}")
def replace_student(
    student_id: Annotated[int, Path(gt=0)],
    student: StudentCreate,
) -> dict[str, Any]:
    for index, existing in enumerate(STUDENTS):
        if existing["id"] == student_id:
            updated = {"id": student_id, **student.model_dump()}
            STUDENTS[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Student not found")


@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> dict[str, Any]:
    return course.model_dump()
