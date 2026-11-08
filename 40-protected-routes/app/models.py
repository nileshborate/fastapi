from datetime import datetime

from sqlalchemy import ForeignKey, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    courses: Mapped[list["Course"]] = relationship(back_populates="owner")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    fee: Mapped[int]
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))     # who created it

    owner: Mapped[User] = relationship(back_populates="courses")
