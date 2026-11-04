# Import every model here, so Base.metadata knows all the tables (Alembic needs this too).
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student
from app.models.teacher import Teacher

__all__ = ["Course", "Enrollment", "Student", "Teacher"]
