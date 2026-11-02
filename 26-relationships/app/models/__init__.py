# Import every model here, so Base.metadata knows all the tables.
from app.models.course import Course
from app.models.teacher import Teacher

__all__ = ["Course", "Teacher"]
