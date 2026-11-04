from sqlalchemy import String, false
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float]
    level: Mapped[str] = mapped_column(String(20), server_default="beginner")   # added by migration 0002
    is_published: Mapped[bool] = mapped_column(server_default=false())          # added by migration 0003 (homework)
