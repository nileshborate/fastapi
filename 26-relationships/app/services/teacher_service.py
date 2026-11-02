from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Teacher
from app.schemas.teacher import TeacherCreate


def list_teachers(db: Session) -> list[Teacher]:
    return list(db.scalars(select(Teacher).order_by(Teacher.id)).all())


def get_teacher(db: Session, teacher_id: int) -> Teacher:
    teacher = db.get(Teacher, teacher_id)
    if teacher is None:
        raise NotFoundError("Teacher")
    return teacher


def create_teacher(db: Session, data: TeacherCreate) -> Teacher:
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def delete_teacher(db: Session, teacher: Teacher) -> None:
    if teacher.courses:                                   # the relationship: a SELECT, then a list
        raise ConflictError(f"Teacher still has {len(teacher.courses)} courses")
    db.delete(teacher)
    db.commit()
