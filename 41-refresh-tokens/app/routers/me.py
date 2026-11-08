# Everything under /me needs a login - the whole router is protected (Video 40)
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.deps import DB, CurrentUser, get_current_active_user
from app.models import RefreshToken, User
from app.schemas import SessionOut, UserOut

router = APIRouter(prefix="/me", tags=["Me"], dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user


@router.get("/sessions", response_model=list[SessionOut])
async def my_sessions(user: CurrentUser, db: DB) -> list[RefreshToken]:
    # every device that is still logged in = every refresh token that is still alive
    stmt = (select(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None),
                   RefreshToken.expires_at > datetime.now(UTC))
            .order_by(RefreshToken.id))
    return list(await db.scalars(stmt))
