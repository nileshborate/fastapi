from typing import TYPE_CHECKING

from sqlalchemy import String, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.database import Base
from app.models.enrollment import Enrollment

if TYPE_CHECKING:
    from app.models.student import Student  # noqa: F401


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    fee: Mapped[float]

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Enrollment.student_id"
    )

    # the average grade - computed by the database, in the same SELECT (NULL grades are ignored)
    average_grade: Mapped[float | None] = column_property(
        select(func.avg(Enrollment.grade)).where(Enrollment.course_id == id).correlate_except(Enrollment).scalar_subquery()
    )
