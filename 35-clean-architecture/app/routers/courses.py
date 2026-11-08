# Router: HTTP only - read the request, call the service, return the answer. That's all.
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.models import Course
from app.schemas import CourseCreate, CourseOut, CourseTransfer, FeeUpdate
from app.services.courses import CourseService
from app.uow import UnitOfWork, get_uow

router = APIRouter(prefix="/courses", tags=["Courses"])


def get_course_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> CourseService:
    return CourseService(uow)


Service = Annotated[CourseService, Depends(get_course_service)]


@router.get("", response_model=list[CourseOut])
async def list_courses(service: Service) -> list[Course]:
    return await service.list()


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: int, service: Service) -> Course:
    return await service.get(course_id)


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseCreate, service: Service) -> Course:
    return await service.create(data)


@router.post("/{course_id}/transfer", response_model=CourseOut)
async def transfer_course(course_id: int, data: CourseTransfer, service: Service) -> Course:
    return await service.transfer(course_id, data.teacher_id)


# ---------------------------------------------------------------- homework answer (Video 35)
@router.patch("/{course_id}/fee", response_model=CourseOut)
async def change_fee(course_id: int, data: FeeUpdate, service: Service) -> Course:
    return await service.change_fee(course_id, data.fee)
