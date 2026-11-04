from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), unique=True)
    fee: Mapped[int]
    seats_left: Mapped[int]
    version: Mapped[int] = mapped_column(default=1)

    # optimistic locking: every UPDATE says "... WHERE id = ? AND version = ?"
    # and sets version + 1. Someone else changed it first? -> StaleDataError
    __mapper_args__ = {"version_id_col": version}
