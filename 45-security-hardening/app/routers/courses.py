# Courses: limited lists, limited bodies, owner checks, limited writes
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.deps import DB, CurrentUser, limit_writes
from app.models import Course
from app.schemas import CourseIn, CourseOut, CourseUpdate

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=list[CourseOut])
async def list_courses(
    db: DB,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,       # never "give me a million"
    offset: Annotated[int, Query(ge=0, le=10_000)] = 0,
    q: Annotated[str | None, Query(max_length=50)] = None,
) -> list[Course]:
    stmt = select(Course).order_by(Course.id).limit(limit).offset(offset)
    if q:
        stmt = stmt.where(Course.title.contains(q, autoescape=True))
    return list(await db.scalars(stmt))


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(limit_writes)])
async def create_course(data: CourseIn, user: CurrentUser, db: DB) -> Course:
    course = Course(**data.model_dump(), owner_id=user.id)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.patch("/{course_id}", response_model=CourseOut, dependencies=[Depends(limit_writes)])
async def update_course(course_id: int, data: CourseUpdate, user: CurrentUser,
                        db: DB) -> Course:
    course = await db.get(Course, course_id)
    if course is None or course.owner_id != user.id:        # OWASP API1: object level
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    await db.commit()
    await db.refresh(course)
    return course
