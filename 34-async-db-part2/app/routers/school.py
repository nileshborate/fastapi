# Teachers and courses - the async CRUD from Video 33, short
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Course, Teacher
from app.schemas import CourseCreate, CourseOut, TeacherCreate, TeacherOut

router = APIRouter(tags=["School"])

DB = Annotated[AsyncSession, Depends(get_db)]


@router.post("/teachers", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
async def create_teacher(data: TeacherCreate, db: DB) -> Teacher:
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    await db.commit()
    return teacher


@router.get("/courses", response_model=list[CourseOut])
async def list_courses(db: DB) -> list[Course]:
    stmt = select(Course).options(selectinload(Course.teacher)).order_by(Course.id)
    return list((await db.scalars(stmt)).all())


@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseCreate, db: DB) -> Course:
    teacher = await db.get(Teacher, data.teacher_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    course = Course(title=data.title, fee=data.fee, teacher=teacher)   # no extra loading
    db.add(course)
    await db.commit()
    return course
