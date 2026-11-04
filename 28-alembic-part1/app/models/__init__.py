# Import every model here, so Base.metadata knows all the tables (Alembic needs this too).
from app.models.course import Course

__all__ = ["Course"]
