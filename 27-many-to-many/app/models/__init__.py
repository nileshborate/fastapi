# Import every model here, so Base.metadata knows all the tables.
from app.models.course import Course
from app.models.enrollment import enrollments
from app.models.student import Student

__all__ = ["Course", "Student", "enrollments"]
