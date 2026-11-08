from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.models import User
from app.schemas import LoginCheck, PasswordChange, UserCreate, UserOut
from app.services.users import UserService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["Users"])


def get_user_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> UserService:
    return UserService(uow)


Service = Annotated[UserService, Depends(get_user_service)]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: Service) -> User:
    return await service.register(data)         # response_model: the hash never leaves


# ---------------------------------------------------------------- homework answer (Video 37)
@router.get("/users", response_model=UserOut)
async def find_user(email: Annotated[str, Query(max_length=254)], service: Service) -> User:
    return await service.find_by_email(email)


@router.patch("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user_id: int, data: PasswordChange, service: Service) -> None:
    await service.change_password(user_id, data.old_password, data.new_password)


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, service: Service) -> User:
    return await service.get(user_id)


@router.post("/auth/check", response_model=UserOut)
async def check_password(data: LoginCheck, service: Service) -> User:
    # a preview - Video 39 turns this into a real login with a token
    return await service.authenticate(data.email, data.password)
