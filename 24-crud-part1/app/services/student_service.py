# Students live in the DATABASE now (homework answer, Video 23)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import AlreadyExistsError, NotFoundError
from app.models import Student
from app.schemas.student import StudentCreate


def list_students(db: Session, skip: int = 0, limit: int = 10) -> list[Student]:
    query = select(Student).order_by(Student.id).offset(skip).limit(limit)
    return list(db.scalars(query).all())


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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("Email already registered") from None
    db.refresh(student)
    return student


def count_students(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Student)) or 0
