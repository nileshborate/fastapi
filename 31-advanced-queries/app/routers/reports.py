from fastapi import APIRouter, Depends, Query
from sqlalchemy import Row
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Student
from app.schemas.report import CourseStats, StudentOut, TeacherStats
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/courses", response_model=list[CourseStats])
def course_stats(
    min_students: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Row]:
    return report_service.course_stats(db, min_students)


@router.get("/teachers", response_model=list[TeacherStats])
def teacher_stats(db: Session = Depends(get_db)) -> list[Row]:
    return report_service.teacher_stats(db)


@router.get("/students-without-courses", response_model=list[StudentOut])
def students_without_courses(db: Session = Depends(get_db)) -> list[Student]:
    return report_service.students_without_courses(db)
