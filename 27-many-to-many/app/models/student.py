from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enrollment import enrollments

if TYPE_CHECKING:
    from app.models.course import Course


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)

    # many-to-many: the rows in "enrollments" connect students and courses
    courses: Mapped[list["Course"]] = relationship(secondary=enrollments, back_populates="students", order_by="Course.id")
