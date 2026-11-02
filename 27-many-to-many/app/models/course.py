from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enrollment import enrollments

if TYPE_CHECKING:
    from app.models.student import Student


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float]

    students: Mapped[list["Student"]] = relationship(secondary=enrollments, back_populates="courses", order_by="Student.id")
