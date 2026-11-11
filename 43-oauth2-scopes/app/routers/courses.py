# Reading needs "courses:read", creating needs "courses:write"
from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.deps import DB, CourseDeleter, CourseReader, CourseWriter
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


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(course_id: int, user: CourseDeleter, db: DB) -> Response:
    # homework 43: only a token with "courses:delete" - and only admins can get that scope
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    await db.delete(course)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
