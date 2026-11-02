# Models = database TABLES (SQLAlchemy).   Schemas = the API's data shapes (Pydantic).
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())   # the DATABASE fills it
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())  # NEW: set on every UPDATE
