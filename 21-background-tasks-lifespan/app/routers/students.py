from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.dependencies import Pagination, SettingsDep, StudentDep, verify_api_key
from app.schemas.student import StudentCreate, StudentOut
from app.services import student_service
from app.tasks import send_welcome_email

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("")
def list_students(page: Pagination) -> list[StudentOut]:
    return student_service.list_students(page.skip, page.limit)


@router.get("/{student_id}")
def get_student(student: StudentDep) -> StudentOut:      # homework answer (Video 17)
    return student


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
def create_student(
    data: StudentCreate,
    background_tasks: BackgroundTasks,              # NEW: FastAPI gives us an empty task list
    settings: SettingsDep,
) -> StudentOut:
    student = student_service.create_student(data)
    background_tasks.add_task(                      # run it LATER - after the response is sent
        send_welcome_email,                         # the function itself - NO brackets
        student.name, student.email, settings.log_file, settings.email_delay_seconds,
    )
    return student                                  # the client gets this right away
