from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.dependencies import DBSession, Pagination, SettingsDep, StudentDep, verify_api_key
from app.models import Student
from app.schemas.student import StudentCreate, StudentOut
from app.services import student_service
from app.tasks import send_welcome_email

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: DBSession, page: Pagination) -> list[Student]:
    return student_service.list_students(db, page.skip, page.limit)


@router.get("/by-email/{email}", response_model=StudentOut)            # NEW: find by a unique field
def get_student_by_email(email: str, db: DBSession) -> Student:
    return student_service.get_student_by_email(db, email)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student: StudentDep) -> Student:
    return student


@router.post(
    "",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
def create_student(
    data: StudentCreate, db: DBSession, background_tasks: BackgroundTasks, settings: SettingsDep
) -> Student:
    student = student_service.create_student(db, data)
    background_tasks.add_task(                      # the welcome email from Video 21
        send_welcome_email,
        student.name, student.email, settings.log_file, settings.email_delay_seconds,
    )
    return student
