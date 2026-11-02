# Import every model here, so Base.metadata knows all the tables.
from app.models.course import Course

__all__ = ["Course"]
