from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    fee: Mapped[float]                                                         # was "price"  (0003: a rename)
    slug: Mapped[str] = mapped_column(String(120), unique=True)                # 0004: a data migration
    level: Mapped[str] = mapped_column(String(20), server_default="beginner")  # 0005: Asha's branch
    description: Mapped[str | None] = mapped_column(Text)                      # 0006: Ravi's branch
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"))  # 0002: batch mode on SQLite

    teacher: Mapped["Teacher | None"] = relationship(back_populates="courses")  # noqa: F821
