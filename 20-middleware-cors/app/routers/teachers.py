from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import Pagination, allow_teachers
from app.schemas.teacher import TeacherCreate, TeacherOut
from app.services import teacher_service

router = APIRouter(prefix="/teachers", tags=["Teachers"], dependencies=[Depends(allow_teachers)])   # homework


@router.get("")
def list_teachers(page: Pagination) -> list[TeacherOut]:          # homework answer (Video 17)
    return teacher_service.list_teachers(page.skip, page.limit)


@router.get("/{teacher_id}")
def get_teacher(teacher_id: int) -> TeacherOut:
    teacher = teacher_service.get_teacher(teacher_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher


@router.post("", status_code=status.HTTP_201_CREATED)
def create_teacher(data: TeacherCreate) -> TeacherOut:
    return teacher_service.create_teacher(data)
