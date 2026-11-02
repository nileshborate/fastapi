from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:                                       # only for the type checker - no circular import
    from app.models.course import Course


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    subject: Mapped[str] = mapped_column(String(50))

    # NOT a column: a Python link to this teacher's courses (the "one" side)
    courses: Mapped[list["Course"]] = relationship(back_populates="teacher", order_by="Course.id")
