from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ConflictError, NotFoundError
from app.models import Course, Teacher
from app.schemas.course import CourseCreate


def list_courses(db: Session, skip: int = 0, limit: int = 10) -> list[Course]:
    query = (
        select(Course)
        .options(selectinload(Course.teacher))            # load ALL their teachers in ONE extra query
        .order_by(Course.id)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(query).all())


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError("Course")
    return course


def create_course(db: Session, data: CourseCreate) -> Course:
    if db.get(Teacher, data.teacher_id) is None:          # check first: a clear 404 for the client
        raise NotFoundError("Teacher")
    course = Course(**data.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Course title already exists") from None
    db.refresh(course)
    return course


def update_course(db: Session, course: Course, changes: dict[str, Any]) -> Course:   # homework (Video 26)
    if "teacher_id" in changes and db.get(Teacher, changes["teacher_id"]) is None:
        raise NotFoundError("Teacher")
    for field, value in changes.items():
        setattr(course, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Course title already exists") from None
    db.refresh(course)                                    # also reloads course.teacher later
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()
