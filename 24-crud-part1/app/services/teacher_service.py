# Teachers live in the DATABASE now (Video 24) - the same pattern as courses and students
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models import Teacher
from app.schemas.teacher import TeacherCreate


def list_teachers(db: Session, skip: int = 0, limit: int = 10) -> list[Teacher]:
    query = select(Teacher).order_by(Teacher.id).offset(skip).limit(limit)
    return list(db.scalars(query).all())


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
