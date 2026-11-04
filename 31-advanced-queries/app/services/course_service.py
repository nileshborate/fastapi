import math

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Course, Teacher
from app.schemas.course import CourseFilters
from app.schemas.page import Page

# homework (Video 31): the allowed sorts - always + Course.id, so the order is unique
SORTS = {
    "id": [Course.id],
    "title": [Course.title, Course.id],
    "fee": [Course.fee, Course.id],
    "-fee": [Course.fee.desc(), Course.id],
}


def course_query(f: CourseFilters) -> Select:
    # 1. the columns we need - from TWO tables
    stmt = select(
        Course.id,
        Course.title,
        Course.level,
        Course.fee,
        Teacher.name.label("teacher"),
    ).join(Course.teacher)      # INNER JOIN teachers ON teachers.id = courses.teacher_id

    # 2. the filters - only the ones that were sent
    if f.q:
        stmt = stmt.where(Course.title.icontains(f.q, autoescape=True))
    if f.level:
        stmt = stmt.where(Course.level == f.level)
    if f.teacher:
        stmt = stmt.where(Teacher.name.icontains(f.teacher, autoescape=True))   # across tables
    if f.max_fee is not None:
        stmt = stmt.where(Course.fee <= f.max_fee)
    return stmt


def search_courses(db: Session, f: CourseFilters) -> Page:
    stmt = course_query(f)

    # 3. the total: COUNT over the SAME query, wrapped as a subquery
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    # 4. one page: ORDER BY (a fixed order!) + LIMIT + OFFSET
    page_stmt = stmt.order_by(*SORTS[f.sort]).limit(f.size).offset((f.page - 1) * f.size)
    rows = db.execute(page_stmt).all()          # Row objects: row.title, row.teacher

    return Page(items=rows, total=total, page=f.page, size=f.size,
                pages=math.ceil(total / f.size))
