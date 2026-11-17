# The same registration twice: email INSIDE the request - and email as a Celery task
from fastapi import APIRouter, HTTPException, status
from pydantic import EmailStr

from app.schemas import Registered, TaskStatus, UserIn
from app.tasks import send_email, send_reminder, send_welcome_email

router = APIRouter(prefix="/users", tags=["Users"])
USERS: dict[str, str] = {}                          # our fake users table


@router.post("/register-slow", status_code=status.HTTP_201_CREATED)
def register_slow(user: UserIn) -> Registered:
    USERS[user.email] = user.name
    send_email(user.email, f"Welcome to Course Hub, {user.name}!")   # the user waits 2 s
    return Registered(email=user.email)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserIn) -> Registered:
    USERS[user.email] = user.name
    task = send_welcome_email.delay(user.email, user.name)   # put it in the queue - don't wait
    return Registered(email=user.email, task_id=task.id)


@router.post("/{email}/reminder", status_code=status.HTTP_202_ACCEPTED)   # homework 52
def remind(email: EmailStr) -> TaskStatus:
    if email not in USERS:                                   # check BEFORE queueing
        raise HTTPException(status_code=404, detail="User not found")
    task = send_reminder.delay(email)
    return TaskStatus(task_id=task.id, state="PENDING")
