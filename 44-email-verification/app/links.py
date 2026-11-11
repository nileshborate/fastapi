# One-time links: a random token in the email, its SHA-256 in the database
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LinkToken, User

# ONE answer for every bad link: unknown, used, expired, wrong purpose - nobody learns why
BAD_LINK = HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                         detail="Invalid or expired link")


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()           # 64 hex characters


async def issue_link(db: AsyncSession, user: User, purpose: str, lifetime: timedelta) -> str:
    """a new link token for this user - every older unused one of the same purpose dies"""
    now = datetime.now(UTC)
    await db.execute(update(LinkToken)
                     .where(LinkToken.user_id == user.id, LinkToken.purpose == purpose,
                            LinkToken.used_at.is_(None))
                     .values(used_at=now))
    raw = secrets.token_urlsafe(32)                            # 32 random bytes = 256 bits
    db.add(LinkToken(user_id=user.id, purpose=purpose, token_hash=hash_token(raw),
                     expires_at=now + lifetime))
    return raw                                                 # goes into the email - ONLY


async def use_link(db: AsyncSession, raw: str, purpose: str) -> User:
    """the token from the link -> its user. Works ONCE, and only before it expires."""
    now = datetime.now(UTC)
    row = await db.scalar(select(LinkToken).where(
        LinkToken.token_hash == hash_token(raw), LinkToken.purpose == purpose,
        LinkToken.used_at.is_(None), LinkToken.expires_at > now))
    if row is None:
        raise BAD_LINK
    row.used_at = now                                          # one time
    user = await db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise BAD_LINK
    return user
