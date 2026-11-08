from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.models import User
from app.schemas import LoginCheck, UserCreate, UserOut
from app.services.users import UserService
from app.uow import UnitOfWork, get_uow

router = APIRouter(tags=["Users"])


def get_user_service(uow: Annotated[UnitOfWork, Depends(get_uow)]) -> UserService:
    return UserService(uow)


Service = Annotated[UserService, Depends(get_user_service)]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, service: Service) -> User:
    return await service.register(data)         # response_model: the hash never leaves


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, service: Service) -> User:
    return await service.get(user_id)


@router.post("/auth/check", response_model=UserOut)
async def check_password(data: LoginCheck, service: Service) -> User:
    # a preview - Video 39 turns this into a real login with a token
    return await service.authenticate(data.email, data.password)
