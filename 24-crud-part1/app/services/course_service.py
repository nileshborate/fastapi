# Services = the business logic. Now they talk to the DATABASE through a session.
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AlreadyExistsError, NotFoundError
from app.models import Course
from app.schemas.course import CourseCreate


def list_courses(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    min_price: float | None = None,
    max_price: float | None = None,
) -> list[Course]:
    query = select(Course)
    if min_price is not None:
        query = query.where(Course.price >= min_price)
    if max_price is not None:
        query = query.where(Course.price <= max_price)
    query = query.order_by(Course.id).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)                # find by primary key
    if course is None:
        raise NotFoundError("Course")                 # NEW: the service decides - main.py -> 404
    return course


def create_course(db: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())              # Pydantic schema -> SQLAlchemy model
    db.add(course)
    try:
        db.commit()                                   # INSERT - saved for real
    except IntegrityError:                            # the UNIQUE rule said no
        db.rollback()                                 # undo - the session is usable again
        raise AlreadyExistsError("Course title already exists") from None
    db.refresh(course)                                # read back the new id + created_at
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()


def count_courses(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Course)) or 0


def load_courses(db: Session, path: Path) -> int:   # used by the lifespan - only into an EMPTY table
    if count_courses(db) > 0:
        return 0
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        db.add(Course(**CourseCreate(**row).model_dump()))
    db.commit()
    return len(rows)
