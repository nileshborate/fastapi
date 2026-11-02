from fastapi import APIRouter, Depends, status

from app.dependencies import DBSession, Pagination, allow_teachers
from app.models import Teacher
from app.schemas.teacher import TeacherCreate, TeacherOut
from app.services import teacher_service

router = APIRouter(prefix="/teachers", tags=["Teachers"], dependencies=[Depends(allow_teachers)])


@router.get("", response_model=list[TeacherOut])
def list_teachers(db: DBSession, page: Pagination) -> list[Teacher]:
    return teacher_service.list_teachers(db, page.skip, page.limit)


@router.get("/{teacher_id}", response_model=TeacherOut)
def get_teacher(teacher_id: int, db: DBSession) -> Teacher:
    return teacher_service.get_teacher(db, teacher_id)          # NotFoundError -> 404


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
def create_teacher(data: TeacherCreate, db: DBSession) -> Teacher:
    return teacher_service.create_teacher(db, data)
