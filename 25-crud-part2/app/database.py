# Database = the connection (engine), a session factory, and the Base class for our models.
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, echo=settings.db_echo)     # ONE engine for the app

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):                    # every model (table) inherits from Base
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()                         # 1. a NEW session for this request
    try:
        yield db                                # 2. the endpoint uses it
    finally:
        db.close()                              # 3. always closed - even after an error
