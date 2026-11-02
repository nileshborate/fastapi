from fastapi import APIRouter, BackgroundTasks, Depends, Response, status

from app.dependencies import (
    DBSession, Pagination, SettingsDep, StudentDep, StudentSearch, require_admin, verify_api_key,
)
from app.models import Student
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.services import student_service
from app.tasks import send_welcome_email

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentOut])
def list_students(db: DBSession, page: Pagination, search: StudentSearch, response: Response) -> list[Student]:
    response.headers["X-Total-Count"] = str(student_service.count_matching(db, search.q))   # homework (Video 25)
    return student_service.list_students(db, page.skip, page.limit, search.q, search.sort_by, search.order)


@router.get("/by-email/{email}", response_model=StudentOut)            # find by a unique field
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


@router.patch("/{student_id}", response_model=StudentOut, dependencies=[Depends(verify_api_key)])   # homework (Video 25)
def update_student(student: StudentDep, data: StudentUpdate, db: DBSession) -> Student:
    return student_service.update_student(db, student, data.model_dump(exclude_unset=True))


@router.delete(                                                                                     # homework (Video 25)
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_api_key), Depends(require_admin)],
)
def delete_student(student: StudentDep, db: DBSession) -> None:
    student_service.delete_student(db, student)
