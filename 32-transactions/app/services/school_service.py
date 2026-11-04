from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.errors import ConflictError, NotFoundError
from app.models import Course, Enrollment, Student
from app.schemas.school import CourseCreate, CourseUpdate, EnrollmentOut, StudentCreate


def create_student(db: Session, data: StudentCreate) -> Student:
    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    return student


def create_course(db: Session, data: CourseCreate) -> Course:
    course = Course(**data.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("Course title already exists") from None
    return course


def get_or_404[T](db: Session, model: type[T], id_: int) -> T:
    obj = db.get(model, id_)
    if obj is None:
        raise NotFoundError(model.__name__)
    return obj


def enroll(db: Session, student_id: int, course_id: int) -> EnrollmentOut:
    """Three changes - ONE transaction: all of them, or none of them."""
    student = get_or_404(db, Student, student_id)
    course = get_or_404(db, Course, course_id)
    try:
        # 1. take a seat - the check and the change in ONE statement (atomic)
        seat = db.execute(
            update(Course)
            .where(Course.id == course.id, Course.seats_left > 0)
            .values(seats_left=Course.seats_left - 1)
        )
        if seat.rowcount == 0:
            raise ConflictError("Course is full")

        # 2. pay - the same idea: only if the balance is enough
        paid = db.execute(
            update(Student)
            .where(Student.id == student.id, Student.balance >= course.fee)
            .values(balance=Student.balance - course.fee)
        )
        if paid.rowcount == 0:
            raise ConflictError("Not enough balance")     # the seat from step 1? rolled back

        # 3. the enrollment itself - the primary key stops a second one
        db.add(Enrollment(student_id=student.id, course_id=course.id))
        db.commit()                                         # ALL three are saved ...
    except IntegrityError:
        db.rollback()                                       # ... or NONE of them
        raise ConflictError("Already enrolled") from None
    except ConflictError:
        db.rollback()
        raise
    db.refresh(student)                                     # read the NEW numbers
    db.refresh(course)
    return EnrollmentOut(student_id=student.id, course_id=course.id,
                         balance=student.balance, seats_left=course.seats_left)


def update_course(db: Session, course: Course, data: CourseUpdate) -> Course:
    if data.version != course.version:                      # the client read an OLD version
        raise ConflictError("Course was changed by someone else - reload it")
    course.fee = data.fee
    try:
        # UPDATE courses SET fee=?, version=? WHERE id = ? AND version = ?
        db.commit()
    except StaleDataError:      # someone changed it between our check and our commit
        db.rollback()
        raise ConflictError("Course was changed by someone else - reload it") from None
    return course
