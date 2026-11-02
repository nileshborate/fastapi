from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, Student
from app.services import course_service, student_service

DBSession = Annotated[Session, Depends(get_db)]


def get_student_or_404(student_id: int, db: DBSession) -> Student:
    return student_service.get_student(db, student_id)


def get_course_or_404(course_id: int, db: DBSession) -> Course:
    return course_service.get_course(db, course_id)


StudentDep = Annotated[Student, Depends(get_student_or_404)]
CourseDep = Annotated[Course, Depends(get_course_or_404)]
