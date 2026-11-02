# Services = the business logic. They talk to the DATABASE through a session.
import json
from pathlib import Path
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AlreadyExistsError, NotFoundError
from app.models import Course
from app.schemas.course import CourseCreate

SORT_COLUMNS = {                                  # NEW: the sort_by text -> a real column
    "id": Course.id,
    "title": Course.title,
    "price": Course.price,
    "created_at": Course.created_at,
}


def _filtered(
    query: Select[Any], min_price: float | None, max_price: float | None, q: str | None
) -> Select[Any]:                                 # the SAME filters for the list AND the count
    if min_price is not None:
        query = query.where(Course.price >= min_price)
    if max_price is not None:
        query = query.where(Course.price <= max_price)
    if q:
        query = query.where(Course.title.icontains(q, autoescape=True))   # NEW: search, any case
    return query


def list_courses(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    min_price: float | None = None,
    max_price: float | None = None,
    q: str | None = None,
    sort_by: str = "id",
    order: str = "asc",
) -> list[Course]:
    query = _filtered(select(Course), min_price, max_price, q)
    column = SORT_COLUMNS[sort_by]
    first = column.desc() if order == "desc" else column.asc()
    query = query.order_by(first, Course.id).offset(skip).limit(limit)   # Course.id = tie-breaker
    return list(db.scalars(query).all())


def count_matching(
    db: Session, min_price: float | None = None, max_price: float | None = None, q: str | None = None
) -> int:                                         # NEW: how many rows match - for X-Total-Count
    query = _filtered(select(func.count()).select_from(Course), min_price, max_price, q)
    return db.scalar(query) or 0


def get_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)                # find by primary key
    if course is None:
        raise NotFoundError("Course")                 # the service decides - main.py -> 404
    return course


def get_course_by_title(db: Session, title: str) -> Course:      # homework answer (Video 24)
    course = db.scalars(select(Course).where(Course.title == title)).first()
    if course is None:
        raise NotFoundError("Course")
    return course


def create_course(db: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())              # Pydantic schema -> SQLAlchemy model
    db.add(course)
    _commit(db, course)
    return course


def update_course(db: Session, course: Course, changes: dict[str, Any]) -> Course:   # NEW
    for field, value in changes.items():              # PUT: every field.  PATCH: only the sent ones
        setattr(course, field, value)                 # change the Python object ...
    _commit(db, course)                               # ... and commit -> UPDATE courses SET ...
    return course


def _commit(db: Session, course: Course) -> None:     # one place for commit + 409 + refresh
    try:
        db.commit()
    except IntegrityError:                            # the UNIQUE rule said no
        db.rollback()                                 # undo - the session is usable again
        raise AlreadyExistsError("Course title already exists") from None
    db.refresh(course)                                # read back id, created_at, updated_at


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)                                 # DELETE FROM courses WHERE id = ...
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
