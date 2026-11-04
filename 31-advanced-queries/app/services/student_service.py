# Homework answer (Video 31)
import math

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.models import Enrollment, Student
from app.schemas.page import Page
from app.schemas.student import StudentFilters


def search_students(db: Session, f: StudentFilters) -> Page:
    stmt = (
        select(
            Student.id,
            Student.name,
            Student.city,
            func.count(Enrollment.course_id).label("courses"),   # NOT count(*)
        )
        .outerjoin(Student.enrollments)                          # Dev: 0 courses
        .group_by(Student.id, Student.name, Student.city)
    )
    if f.city:
        stmt = stmt.where(Student.city == f.city)               # WHERE: before grouping
    # a GROUP BY inside a page: the total counts the GROUPS - one row per student
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    page_stmt = stmt.order_by(Student.id).limit(f.size).offset((f.page - 1) * f.size)
    rows = db.execute(page_stmt).all()
    return Page(items=rows, total=total, page=f.page, size=f.size,
                pages=math.ceil(total / f.size))


def top_students(db: Session, limit: int) -> list[Row]:
    average = func.avg(Enrollment.grade).label("average_grade")
    stmt = (
        select(Student.name, average)
        .join(Student.enrollments)                       # only students WITH enrollments
        .where(Enrollment.grade.is_not(None))            # only graded ones
        .group_by(Student.id, Student.name)
        .order_by(average.desc(), Student.id)
        .limit(limit)
    )
    return list(db.execute(stmt).all())
