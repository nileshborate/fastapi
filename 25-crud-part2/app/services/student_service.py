# Students live in the DATABASE now (homework answer, Video 23)
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AlreadyExistsError, NotFoundError
from app.models import Student
from app.schemas.student import StudentCreate


SORT_COLUMNS = {"id": Student.id, "name": Student.name, "email": Student.email, "created_at": Student.created_at}


def _filtered(query: Select[Any], q: str | None) -> Select[Any]:          # homework answer (Video 25)
    if q:
        query = query.where(Student.name.icontains(q, autoescape=True))
    return query


def list_students(
    db: Session, skip: int = 0, limit: int = 10, q: str | None = None, sort_by: str = "id", order: str = "asc"
) -> list[Student]:
    column = SORT_COLUMNS[sort_by]
    first = column.desc() if order == "desc" else column.asc()
    query = _filtered(select(Student), q).order_by(first, Student.id).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def count_matching(db: Session, q: str | None = None) -> int:
    return db.scalar(_filtered(select(func.count()).select_from(Student), q)) or 0


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFoundError("Student")
    return student


def get_student_by_email(db: Session, email: str) -> Student:      # NEW: find by a UNIQUE column
    student = db.scalars(select(Student).where(Student.email == email)).first()
    if student is None:
        raise NotFoundError("Student")
    return student


def create_student(db: Session, data: StudentCreate) -> Student:
    student = Student(**data.model_dump())
    db.add(student)
    _commit(db, student)
    return student


def update_student(db: Session, student: Student, changes: dict[str, Any]) -> Student:   # homework (Video 25)
    for field, value in changes.items():
        setattr(student, field, value)
    _commit(db, student)
    return student


def delete_student(db: Session, student: Student) -> None:                              # homework (Video 25)
    db.delete(student)
    db.commit()


def _commit(db: Session, student: Student) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("Email already registered") from None
    db.refresh(student)


def count_students(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Student)) or 0
