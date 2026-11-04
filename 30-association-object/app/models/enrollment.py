# The ASSOCIATION OBJECT: the link between a student and a course is now a class - with its own data
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.student import Student


class Enrollment(Base):
    __tablename__ = "enrollments"

    # the same two columns as the link table - together the primary key
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)

    # NEW: the link's own data
    enrolled_at: Mapped[datetime] = mapped_column(server_default=func.now())   # the DATABASE fills it
    grade: Mapped[int | None]                                                  # 0-100, set later
    # homework (Video 30): active / completed / dropped
    status: Mapped[str] = mapped_column(String(20), server_default="active")

    # one enrollment -> one student, one course
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
