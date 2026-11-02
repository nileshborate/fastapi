from sqlalchemy import String, func, select
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.database import Base
from app.models.course import Course                    # homework (Video 26): needed at runtime for the count


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(50))

    # NOT a column: a Python link to this teacher's courses (the "one" side)
    courses: Mapped[list["Course"]] = relationship(back_populates="teacher", order_by="Course.id")

    # homework answer (Video 26): counted INSIDE the same SELECT - no extra query, no N+1
    course_count: Mapped[int] = column_property(
        select(func.count(Course.id)).where(Course.teacher_id == id).correlate_except(Course).scalar_subquery()
    )
