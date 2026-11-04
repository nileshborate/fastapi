# Import every model here, so Base.metadata knows all the tables (Alembic needs this too).
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.student import Student

__all__ = ["Course", "Enrollment", "Student"]
