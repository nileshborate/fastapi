from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.errors import ConflictError, NotFoundError
from app.models import Course, Enrollment, Student
from app.schemas.student import StudentCreate


def list_students(db: Session) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.id)).all())


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFoundError("Student")
    return student


def get_student_detail(db: Session, student_id: int) -> Student:
    # the student + the enrollments + each enrollment's course: 3 queries, whatever the number of courses
    stmt = (
        select(Student)
        .where(Student.id == student_id)
        .options(selectinload(Student.enrollments).selectinload(Enrollment.course))
    )
    student = db.scalars(stmt).one_or_none()
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
        raise ConflictError("Email already registered") from None
    db.refresh(student)
    return student


def delete_student(db: Session, student: Student) -> None:
    db.delete(student)                       # cascade="all, delete-orphan": the enrollments go too
    db.commit()


# ---------------------------------------------------------------- enrollments
def get_enrollment(db: Session, student_id: int, course_id: int) -> Enrollment:
    enrollment = db.get(Enrollment, (student_id, course_id))     # composite primary key -> a tuple
    if enrollment is None:
        raise NotFoundError("Enrollment")
    return enrollment


def enroll(db: Session, student: Student, course: Course) -> Enrollment:
    if db.get(Enrollment, (student.id, course.id)) is not None:
        raise ConflictError("Already enrolled")
    enrollment = Enrollment(student=student, course=course)     # an OBJECT now - not list.append(course)
    db.add(enrollment)
    db.commit()                              # INSERT ... RETURNING enrolled_at: the date comes back at once
    return enrollment


def set_grade(db: Session, enrollment: Enrollment, grade: int) -> Enrollment:
    enrollment.grade = grade                 # UPDATE enrollments SET grade=? WHERE student_id=? AND course_id=?
    db.commit()
    db.refresh(enrollment.course)            # the course's average_grade changed
    return enrollment


def unenroll(db: Session, enrollment: Enrollment) -> None:
    db.delete(enrollment)                    # DELETE FROM enrollments WHERE student_id=? AND course_id=?
    db.commit()
