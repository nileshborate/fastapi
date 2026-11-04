from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ConflictError, NotFoundError
from app.models import Course, Enrollment
from app.schemas.course import CourseCreate


def list_courses(db: Session) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.id)).all())


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise NotFoundError("Course")
    return course


def get_course_detail(db: Session, course_id: int) -> Course:
    stmt = (
        select(Course)
        .where(Course.id == course_id)
        .options(selectinload(Course.enrollments).selectinload(Enrollment.student))
    )
    course = db.scalars(stmt).one_or_none()
    if course is None:
        raise NotFoundError("Course")
    return course


def create_course(db: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Course title already exists") from None
    db.refresh(course)
    return course
