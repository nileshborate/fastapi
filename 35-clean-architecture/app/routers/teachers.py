from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.models import Teacher
from app.schemas import TeacherCreate, TeacherOut
from app.services.teachers import TeacherService
from app.uow import UnitOfWork, get_uow

router = APIRouter(prefix="/teachers", tags=["Teachers"])


def get_teacher_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> TeacherService:
    return TeacherService(uow)


Service = Annotated[TeacherService, Depends(get_teacher_service)]


@router.get("", response_model=list[TeacherOut])
async def list_teachers(service: Service) -> list[Teacher]:
    return await service.list()


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
async def create_teacher(data: TeacherCreate, service: Service) -> Teacher:
    return await service.create(data)
