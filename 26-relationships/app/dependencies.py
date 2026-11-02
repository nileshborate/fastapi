from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, Teacher
from app.services import course_service, teacher_service

DBSession = Annotated[Session, Depends(get_db)]


class PaginationParams:
    def __init__(
        self,
        skip: Annotated[int, Query(ge=0)] = 0,
        limit: Annotated[int, Query(ge=1, le=100)] = 10,
    ) -> None:
        self.skip = skip
        self.limit = limit


Pagination = Annotated[PaginationParams, Depends()]


def get_teacher_or_404(teacher_id: int, db: DBSession) -> Teacher:
    return teacher_service.get_teacher(db, teacher_id)


def get_course_or_404(course_id: int, db: DBSession) -> Course:
    return course_service.get_course(db, course_id)


TeacherDep = Annotated[Teacher, Depends(get_teacher_or_404)]
CourseDep = Annotated[Course, Depends(get_course_or_404)]
