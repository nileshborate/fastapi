from fastapi import APIRouter, HTTPException, status

from app.schemas.student import StudentCreate, StudentOut
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("")
def list_students() -> list[StudentOut]:
    return student_service.list_students()


@router.get("/{student_id}")
def get_student(student_id: int) -> StudentOut:
    student = student_service.get_student(student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.post("", status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate) -> StudentOut:
    return student_service.create_student(data)
