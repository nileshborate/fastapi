from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, Enrollment, Student
from app.services import course_service, student_service

DBSession = Annotated[Session, Depends(get_db)]


def get_student_or_404(student_id: int, db: DBSession) -> Student:
    return student_service.get_student(db, student_id)


def get_course_or_404(course_id: int, db: DBSession) -> Course:
    return course_service.get_course(db, course_id)


def get_enrollment_or_404(student_id: int, course_id: int, db: DBSession) -> Enrollment:
    return student_service.get_enrollment(db, student_id, course_id)


StudentDep = Annotated[Student, Depends(get_student_or_404)]
CourseDep = Annotated[Course, Depends(get_course_or_404)]
EnrollmentDep = Annotated[Enrollment, Depends(get_enrollment_or_404)]
