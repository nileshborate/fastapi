# Part 2: the same "courses" table with the SQLAlchemy 2.0 ORM - Python classes instead of SQL.
# Run (from the 22-databases-orms folder):  python -m db_basics.orm_basics
from pathlib import Path

from sqlalchemy import Engine, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):                     # every model (table class) inherits from Base
    pass


class Course(Base):                              # a class   = a table
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)                 # an attribute = a column
    title: Mapped[str] = mapped_column(String(100), unique=True)
    price: Mapped[float]

    def __repr__(self) -> str:
        return f"Course(id={self.id}, title={self.title!r}, price={self.price})"


def make_engine(url: str = "sqlite:///school_orm.db", echo: bool = False) -> Engine:
    engine = create_engine(url, echo=echo)      # echo=True prints every SQL statement
    Base.metadata.create_all(engine)             # CREATE TABLE for every model
    return engine


def main() -> None:
    Path("school_orm.db").unlink(missing_ok=True)
    engine = make_engine(echo=True)
    with Session(engine) as session:             # a session = one conversation with the database
        session.add_all([                        # an object = a row
            Course(title="FastAPI Basics", price=299),
            Course(title="Pydantic Models", price=199),
            Course(title="Async Python", price=249),
        ])
        session.commit()                         # INSERT ... - saved for real

        query = select(Course).where(Course.price < 250).order_by(Course.title)    # SELECT ... WHERE
        cheap = session.scalars(query).all()     # a list of Course objects
        print("Under 250:", cheap)

        course = session.get(Course, 1)          # find by primary key
        if course is not None:
            course.price = 349                   # UPDATE: just change the attribute
            session.commit()
            print("Updated:", course)


if __name__ == "__main__":
    main()
