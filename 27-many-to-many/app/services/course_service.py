from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Course
from app.schemas.course import CourseCreate


def list_courses(db: Session) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.id)).all())


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
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


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)                        # its enrollments go too - the students stay
    db.commit()
