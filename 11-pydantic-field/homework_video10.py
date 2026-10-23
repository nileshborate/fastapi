# Answer to the Video 10 homework: StudentCreate + POST /students + PUT /students/{student_id}
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel

app = FastAPI(title="Course Hub API", version="1.3.0")


class StudentCreate(BaseModel):
    name: str
    email: str
    age: int | None = None
    courses: list[int] = []      # Pydantic copies this default, so it's safe


STUDENTS: list[dict[str, Any]] = []


def next_id() -> int:
    return max((student["id"] for student in STUDENTS), default=0) + 1


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
