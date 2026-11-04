from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Teacher
from app.schemas.school import TeacherCreate, TeacherOut

router = APIRouter(prefix="/teachers", tags=["Teachers"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[TeacherOut])
async def list_teachers(db: DB) -> list[Teacher]:
    result = await db.scalars(select(Teacher).order_by(Teacher.id))
    return list(result.all())


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
async def create_teacher(data: TeacherCreate, db: DB) -> Teacher:
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    await db.commit()
    return teacher                  # expire_on_commit=False: teacher.name needs no new query
