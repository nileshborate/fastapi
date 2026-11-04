from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Course, Teacher
from app.schemas.school import CourseCreate, CourseOut, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])

DB = Annotated[AsyncSession, Depends(get_db)]

# every course query loads the teacher too - in the SAME await (no lazy loading in async)
WITH_TEACHER = selectinload(Course.teacher)


@router.get("", response_model=list[CourseOut])
async def list_courses(db: DB) -> list[Course]:
    result = await db.scalars(select(Course).options(WITH_TEACHER).order_by(Course.id))
    return list(result.all())


@router.get("/{course_id}", response_model=CourseOut)
async def get_course(course_id: int, db: DB) -> Course:
    course = await db.get(Course, course_id, options=[WITH_TEACHER])
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseCreate, db: DB) -> Course:
    if await db.get(Teacher, data.teacher_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    course = Course(**data.model_dump())
    db.add(course)                          # no await: it only remembers the object
    try:
        await db.commit()                   # await: talks to the database
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Course title already exists") from None
    await db.refresh(course, attribute_names=["teacher"])     # load the teacher for the answer
    return course


# ---------------------------------------------------------------- homework answer (Video 33)
@router.patch("/{course_id}", response_model=CourseOut)
async def update_course(course_id: int, data: CourseUpdate, db: DB) -> Course:
    course = await db.get(Course, course_id, options=[WITH_TEACHER])
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    course.fee = data.fee                   # just Python - no await
    await db.commit()                       # the UPDATE runs here
    return course                           # expire_on_commit=False: teacher still loaded
