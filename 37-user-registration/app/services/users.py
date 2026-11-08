# The rules for accounts: unique email, only hashes, the same answer for every login failure
from app.errors import AuthError, ConflictError, NotFoundError
from app.models import User
from app.schemas import UserCreate
from app.security import DUMMY_HASH, hash_password, verify_password
from app.uow import UnitOfWork

LOGIN_FAILED = "Wrong email or password"


class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def register(self, data: UserCreate) -> User:
        if await self.uow.users.get_by_email(data.email) is not None:
            raise ConflictError("Email already registered")
        user = User(email=data.email, full_name=data.full_name,
                    password_hash=hash_password(data.password))    # hash it - right here
        self.uow.users.add(user)
        await self.uow.commit()             # the unique index is the last safety net
        await self.uow.db.refresh(user)     # id, is_active, created_at from the database
        return user

    async def get(self, user_id: int) -> User:
        user = await self.uow.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.uow.users.get_by_email(email)
        if user is None:
            verify_password(password, DUMMY_HASH)       # same work = same time
            raise AuthError(LOGIN_FAILED)
        ok, new_hash = verify_password(password, user.password_hash)
        if not ok or not user.is_active:
            raise AuthError(LOGIN_FAILED)
        if new_hash is not None:                        # an old (bcrypt) hash: upgrade it
            user.password_hash = new_hash
            await self.uow.commit()
        return user
