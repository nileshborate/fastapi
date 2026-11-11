from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'teacher', 'student')", name="role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    role: Mapped[str] = mapped_column(String(20), server_default="student")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    fee: Mapped[int]
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
