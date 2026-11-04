from fastapi import APIRouter, status

from app.dependencies import DBSession, EnrollmentDep, StudentDep
from app.models import Course, Enrollment, Student
from app.schemas.course import CourseOut
from app.schemas.enrollment import EnrollmentCreate, EnrollmentOut, GradeUpdate, StudentDetail
from app.schemas.student import StudentCreate, StudentOut
from app.services import course_service, student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: DBSession) -> list[Student]:
    return student_service.list_students(db)


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: DBSession) -> Student:
    return student_service.create_student(db, data)


@router.get("/{student_id}", response_model=StudentDetail)              # + enrollments (course, enrolled_at, grade)
def get_student(student_id: int, db: DBSession) -> Student:
    return student_service.get_student_detail(db, student_id)


@router.get("/{student_id}/courses", response_model=list[CourseOut])    # the association proxy
def list_student_courses(student: StudentDep) -> list[Course]:
    return list(student.courses)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student: StudentDep, db: DBSession) -> None:
    student_service.delete_student(db, student)


# ---------------------------------------------------------------- enrollments: the association object
@router.post("/{student_id}/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def enroll(student: StudentDep, data: EnrollmentCreate, db: DBSession) -> Enrollment:
    course = course_service.get_course(db, data.course_id)               # 404 "Course not found"
    return student_service.enroll(db, student, course)


@router.patch("/{student_id}/enrollments/{course_id}", response_model=EnrollmentOut)
def set_grade(enrollment: EnrollmentDep, data: GradeUpdate, db: DBSession) -> Enrollment:
    return student_service.set_grade(db, enrollment, data.grade)


@router.delete("/{student_id}/enrollments/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll(enrollment: EnrollmentDep, db: DBSession) -> None:
    student_service.unenroll(db, enrollment)
