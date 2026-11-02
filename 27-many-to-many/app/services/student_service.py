from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError, NotFoundError
from app.models import Course, Student
from app.schemas.student import StudentCreate


def list_students(db: Session) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.id)).all())


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
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
    db.delete(student)                       # SQLAlchemy ALSO deletes this student's rows in "enrollments"
    db.commit()


def enroll(db: Session, student: Student, course: Course) -> Student:
    if course in student.courses:            # loads the student's courses (one SELECT)
        raise ConflictError("Already enrolled")
    student.courses.append(course)           # just a Python list ...
    db.commit()                              # ... -> INSERT INTO enrollments (student_id, course_id)
    return student


def unenroll(db: Session, student: Student, course: Course) -> None:
    if course not in student.courses:
        raise NotFoundError("Enrollment")
    student.courses.remove(course)           # -> DELETE FROM enrollments WHERE student_id = ? AND course_id = ?
    db.commit()
