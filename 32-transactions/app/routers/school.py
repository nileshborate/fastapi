from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, Student
from app.schemas.school import (
    CourseCreate,
    CourseOut,
    CourseUpdate,
    EnrollmentCreate,
    EnrollmentOut,
    StudentCreate,
    StudentOut,
    TopUp,
)
from app.services import school_service as service

router = APIRouter()


@router.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED,
             tags=["Students"])
def create_student(data: StudentCreate, db: Session = Depends(get_db)) -> Student:
    return service.create_student(db, data)


@router.get("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)) -> Student:
    return service.get_or_404(db, Student, student_id)


@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED,
             tags=["Courses"])
def create_course(data: CourseCreate, db: Session = Depends(get_db)) -> Course:
    return service.create_course(db, data)


@router.get("/courses/{course_id}", response_model=CourseOut, tags=["Courses"])
def get_course(course_id: int, db: Session = Depends(get_db)) -> Course:
    return service.get_or_404(db, Course, course_id)


@router.patch("/courses/{course_id}", response_model=CourseOut, tags=["Courses"])
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)) -> Course:
    course = service.get_or_404(db, Course, course_id)
    return service.update_course(db, course, data)        # 409 if the version is old


@router.post("/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED,
             tags=["Enrollments"])
def enroll(data: EnrollmentCreate, db: Session = Depends(get_db)) -> EnrollmentOut:
    return service.enroll(db, data.student_id, data.course_id)


# ---------------------------------------------------------------- homework answer (Video 32)
@router.delete("/enrollments/{student_id}/{course_id}", status_code=status.HTTP_204_NO_CONTENT,
               tags=["Enrollments"])
def unenroll(student_id: int, course_id: int, db: Session = Depends(get_db)) -> None:
    service.unenroll(db, student_id, course_id)


@router.post("/students/{student_id}/top-up", response_model=StudentOut, tags=["Students"])
def top_up(student_id: int, data: TopUp, db: Session = Depends(get_db)) -> Student:
    return service.top_up(db, student_id, data)
