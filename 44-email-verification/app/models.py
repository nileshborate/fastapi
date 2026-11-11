from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    is_verified: Mapped[bool] = mapped_column(server_default=false())      # NEW
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class LinkToken(Base):
    """One row per link we emailed. We store the token's SHA-256 - never the token itself."""
    __tablename__ = "link_tokens"
    __table_args__ = (CheckConstraint("purpose IN ('verify', 'reset')", name="purpose"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(10))              # "verify" or "reset"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))   # one time
