from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.models import Course, Enrollment, Student, Teacher


def course_stats(db: Session, min_students: int = 0) -> list[Row]:
    students = func.count(Enrollment.student_id).label("students")   # NOT count(*)
    stmt = (
        select(
            Course.title,
            Teacher.name.label("teacher"),
            students,
            func.avg(Enrollment.grade).label("average_grade"),
        )
        .join(Course.teacher)
        .outerjoin(Course.enrollments)      # LEFT OUTER JOIN: courses with 0 students stay
        .group_by(Course.id, Course.title, Teacher.name)
        .order_by(students.desc(), Course.id)
    )
    if min_students:
        stmt = stmt.having(students >= min_students)    # a filter AFTER grouping
    return list(db.execute(stmt).all())


def teacher_stats(db: Session) -> list[Row]:
    stmt = (
        select(
            Teacher.name.label("teacher"),
            func.count(Course.id.distinct()).label("courses"),
            func.count(Enrollment.student_id.distinct()).label("students"),
        )
        .outerjoin(Teacher.courses)
        .outerjoin(Course.enrollments)
        .group_by(Teacher.id, Teacher.name)
        .order_by(Teacher.id)
    )
    return list(db.execute(stmt).all())


def students_without_courses(db: Session) -> list[Student]:
    # WHERE NOT EXISTS (SELECT 1 FROM enrollments WHERE enrollments.student_id = students.id)
    stmt = select(Student).where(~Student.enrollments.any()).order_by(Student.id)
    return list(db.scalars(stmt).all())
