# Everything under /me needs a login - the whole router is protected (Video 40)
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.deps import DB, CurrentUser, get_current_active_user
from app.models import RefreshToken, User
from app.schemas import PasswordChange, SessionOut, TokenPair, UserOut
from app.security import hash_password, verify_password
from app.tokens import issue_pair, revoke_all

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


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_session(session_id: int, user: CurrentUser, db: DB) -> Response:
    # homework 41: log out ONE device. Somebody else's session: 404 (like Video 40)
    stmt = select(RefreshToken).where(RefreshToken.id == session_id,
                                      RefreshToken.user_id == user.id,
                                      RefreshToken.revoked_at.is_(None))
    row = await db.scalar(stmt)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    row.revoked_at = datetime.now(UTC)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/password", response_model=TokenPair)
async def change_password(data: PasswordChange, user: CurrentUser, db: DB) -> TokenPair:
    # homework 41: a new password logs out EVERYWHERE - a thief with an old token is out too
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Old password is wrong")
    user.password_hash = hash_password(data.new_password)
    await revoke_all(db, user.id)                     # every refresh token dies
    user.token_version += 1                           # every access token dies
    pair, _ = await issue_pair(db, user)              # ...but THIS device stays logged in
    await db.commit()
    return pair
