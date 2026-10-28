from fastapi import APIRouter, Depends, status

from app.dependencies import Pagination, StudentDep, verify_api_key
from app.schemas.student import StudentCreate, StudentOut
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("")
def list_students(page: Pagination) -> list[StudentOut]:
    return student_service.list_students(page.skip, page.limit)


@router.get("/{student_id}")
def get_student(student: StudentDep) -> StudentOut:      # homework answer (Video 17)
    return student


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
def create_student(data: StudentCreate) -> StudentOut:
    return student_service.create_student(data)
