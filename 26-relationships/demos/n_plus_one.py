# The N+1 problem - run it:  python -m demos.n_plus_one
from typing import Any

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, selectinload

from app.database import Base
from app.models import Course, Teacher

engine = create_engine("sqlite://")                    # a database in MEMORY - just for this demo
Base.metadata.create_all(engine)
queries: list[str] = []


@event.listens_for(engine, "before_cursor_execute")
def count(conn: Any, cursor: Any, statement: str, *args: Any) -> None:
    queries.append(statement.split()[0])               # remember every SQL statement


with Session(engine) as db:
    for i in range(1, 6):
        teacher = Teacher(name=f"Teacher {i}", subject="Python")
        db.add(Course(title=f"Course {i}", price=99, teacher=teacher))   # set the RELATIONSHIP
    db.commit()

for name, query in [("lazy (default)", select(Course)),
                    ("selectinload", select(Course).options(selectinload(Course.teacher)))]:
    with Session(engine) as db:
        queries.clear()
        for course in db.scalars(query):
            course.teacher.name                        # touch the teacher of every course
        print(f"{name:15} 5 courses -> {len(queries)} SELECT queries")
