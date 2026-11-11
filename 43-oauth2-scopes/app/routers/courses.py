# Reading needs "courses:read", creating needs "courses:write"
from fastapi import APIRouter, status
from sqlalchemy import select

from app.deps import DB, CourseReader, CourseWriter
from app.models import Course
from app.schemas import CourseIn, CourseOut

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseOut])
async def list_courses(user: CourseReader, db: DB) -> list[Course]:
    return list(await db.scalars(select(Course).order_by(Course.id)))


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
async def create_course(data: CourseIn, user: CourseWriter, db: DB) -> Course:
    course = Course(**data.model_dump(), teacher_id=user.id)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course
