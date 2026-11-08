# Import every model here, so Base.metadata knows all the tables (Alembic needs this too).
from app.models.user import User

__all__ = ["User"]
