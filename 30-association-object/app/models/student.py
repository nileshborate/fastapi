from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.enrollment import Enrollment


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)

    # one-to-many to the association object (not secondary= any more)
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan", order_by="Enrollment.course_id"
    )

    # a shortcut: student.courses = [e.course for e in student.enrollments]  (read only here)
    courses: AssociationProxy[list["Course"]] = association_proxy("enrollments", "course")
