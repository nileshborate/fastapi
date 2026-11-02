# Import every model here, so Base.metadata knows all the tables.
from app.models.course import Course
from app.models.student import Student
from app.models.teacher import Teacher

__all__ = ["Course", "Student", "Teacher"]
