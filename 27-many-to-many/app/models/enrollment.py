# The LINK table: one row = one student enrolled in one course
from sqlalchemy import Column, ForeignKey, Table

from app.database import Base

enrollments = Table(
    "enrollments",
    Base.metadata,                                              # the same metadata as our models
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)   # primary key = (student_id, course_id)  ->  the same pair can't be saved twice
