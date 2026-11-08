# Hand out, rotate and revoke refresh tokens - the rules live HERE, not in the routes
from datetime import UTC, datetime

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import RefreshToken, User
from app.schemas import TokenPair
from app.security import create_access_token, create_refresh_token, decode_token


def refresh_error(detail: str = "Invalid refresh token") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail,
                         headers={"WWW-Authenticate": "Bearer"})


async def issue_pair(db: AsyncSession, user: User) -> tuple[TokenPair, RefreshToken]:
    """a new access token + a new refresh token, and a row for the refresh token"""
    refresh, jti, expires = create_refresh_token(user.id)
    row = RefreshToken(jti=jti, user_id=user.id, created_at=datetime.now(UTC),
                       expires_at=expires)
    db.add(row)
    minutes = get_settings().access_token_minutes
    pair = TokenPair(access_token=create_access_token(user.id, user.token_version),
                     refresh_token=refresh, expires_in=minutes * 60)
    return pair, row


async def revoke_all(db: AsyncSession, user_id: int) -> int:
    """revoke every refresh token of this user that is still alive"""
    result = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC)))
    return result.rowcount


async def find_row(db: AsyncSession, token: str) -> RefreshToken:
    try:
        claims = decode_token(token, "refresh")             # signature, exp, type
    except jwt.InvalidTokenError:
        raise refresh_error() from None
    row = await db.scalar(select(RefreshToken).where(RefreshToken.jti == claims["jti"]))
    if row is None:                                         # we never issued it
        raise refresh_error()
    return row


async def rotate(db: AsyncSession, token: str) -> TokenPair:
    """an old refresh token in, a NEW pair out - and the old one is dead"""
    row = await find_row(db, token)
    if row.replaced_by is not None:
        # this token was ALREADY used for a refresh - so somebody has a copy of it.
        # We can't tell who is the thief, so we log the user out EVERYWHERE.
        await revoke_all(db, row.user_id)
        await db.commit()
        raise refresh_error("Refresh token reuse detected")
    if row.revoked_at is not None:                          # logged out
        raise refresh_error("Refresh token revoked")
    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise refresh_error()
    pair, new_row = await issue_pair(db, user)
    row.revoked_at = datetime.now(UTC)                       # one use only
    row.replaced_by = new_row.jti                            # the chain: old -> new
    await db.commit()
    return pair
