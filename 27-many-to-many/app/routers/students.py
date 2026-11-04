from fastapi import APIRouter, status

from app.dependencies import CourseDep, DBSession, StudentDep
from app.models import Course, Student
from app.schemas.details import StudentDetail
from app.schemas.course import CourseOut
from app.schemas.student import StudentCreate, StudentOut
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: DBSession) -> list[Student]:
    return student_service.list_students(db)


@router.get("/{student_id}", response_model=StudentDetail)              # the student + the courses
def get_student(student: StudentDep) -> Student:
    return student


@router.get("/{student_id}/courses", response_model=list[CourseOut])    # homework answer (Video 27)
def list_student_courses(student: StudentDep) -> list[Course]:
    return student.courses


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: DBSession) -> Student:
    return student_service.create_student(db, data)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student: StudentDep, db: DBSession) -> None:
    student_service.delete_student(db, student)


# ---------------------------------------------------------------- enrollments: a student + a course
@router.post("/{student_id}/courses/{course_id}", response_model=StudentDetail, status_code=status.HTTP_201_CREATED)
def enroll(student: StudentDep, course: CourseDep, db: DBSession) -> Student:
    return student_service.enroll(db, student, course)


@router.delete("/{student_id}/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll(student: StudentDep, course: CourseDep, db: DBSession) -> None:
    student_service.unenroll(db, student, course)
