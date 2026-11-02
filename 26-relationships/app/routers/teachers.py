from fastapi import APIRouter, status

from app.dependencies import DBSession, TeacherDep
from app.models import Course, Teacher
from app.schemas.course import CourseOut
from app.schemas.teacher import TeacherCreate, TeacherDetail, TeacherOut
from app.services import teacher_service

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.get("", response_model=list[TeacherDetail] | list[TeacherOut])        # homework answer (Video 26)
def list_teachers(db: DBSession, with_courses: bool = False) -> list[TeacherDetail] | list[TeacherOut]:
    teachers = teacher_service.list_teachers(db, with_courses)
    if with_courses:
        return [TeacherDetail.model_validate(t) for t in teachers]
    return [TeacherOut.model_validate(t) for t in teachers]


@router.get("/{teacher_id}", response_model=TeacherDetail)        # the teacher + the courses
def get_teacher(teacher: TeacherDep) -> Teacher:
    return teacher


@router.get("/{teacher_id}/courses", response_model=list[CourseOut])
def list_teacher_courses(teacher: TeacherDep) -> list[Course]:
    return teacher.courses                                        # the relationship does the query


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
def create_teacher(data: TeacherCreate, db: DBSession) -> Teacher:
    return teacher_service.create_teacher(db, data)


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(teacher: TeacherDep, db: DBSession) -> None:
    teacher_service.delete_teacher(db, teacher)                   # 409 if the teacher has courses
