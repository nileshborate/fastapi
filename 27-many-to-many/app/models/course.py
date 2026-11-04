from typing import TYPE_CHECKING

from sqlalchemy import String, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.database import Base
from app.models.enrollment import enrollments

if TYPE_CHECKING:
    from app.models.student import Student


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float]
    max_students: Mapped[int] = mapped_column(default=30)        # homework answer (Video 27)

    students: Mapped[list["Student"]] = relationship(secondary=enrollments, back_populates="courses", order_by="Student.id")

    # homework answer (Video 27): counted inside the same SELECT
    student_count: Mapped[int] = column_property(
        select(func.count()).where(enrollments.c.course_id == id).correlate_except(enrollments).scalar_subquery()
    )
