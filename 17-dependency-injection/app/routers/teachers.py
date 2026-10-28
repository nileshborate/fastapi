# Homework answer from Video 16 - the teachers module
from fastapi import APIRouter, HTTPException, status

from app.schemas.teacher import TeacherCreate, TeacherOut
from app.services import teacher_service

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.get("")
def list_teachers() -> list[TeacherOut]:
    return teacher_service.list_teachers()


@router.get("/{teacher_id}")
def get_teacher(teacher_id: int) -> TeacherOut:
    teacher = teacher_service.get_teacher(teacher_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return teacher


@router.post("", status_code=status.HTTP_201_CREATED)
def create_teacher(data: TeacherCreate) -> TeacherOut:
    return teacher_service.create_teacher(data)
