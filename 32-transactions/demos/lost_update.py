# Two requests, one row - played step by step with TWO sessions (= two requests)
# Run (from the 32-transactions folder):  python -m demos.lost_update
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./demo.db")   # a throw-away database

from sqlalchemy import select, update  # noqa: E402
from sqlalchemy.dialects import postgresql, sqlite  # noqa: E402
from sqlalchemy.orm.exc import StaleDataError  # noqa: E402

from app import models  # noqa: E402, F401
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Course  # noqa: E402


def reset() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(Course(id=1, title="FastAPI Basics", fee=299, seats_left=1))
        db.commit()


def seats() -> int:
    with SessionLocal() as db:
        return db.get(Course, 1).seats_left


# ---- 1. read - change in Python - write: the LOST UPDATE
reset()
a, b = SessionLocal(), SessionLocal()
course_a = a.get(Course, 1)                 # request A reads: 1 seat left
course_b = b.get(Course, 1)                 # request B reads: 1 seat left
if course_a.seats_left > 0:
    a.execute(update(Course).where(Course.id == 1).values(seats_left=course_a.seats_left - 1))
    a.commit()                              # A: seats_left = 0, "you got it!"
if course_b.seats_left > 0:                 # B still sees 1 - an OLD value
    b.execute(update(Course).where(Course.id == 1).values(seats_left=course_b.seats_left - 1))
    b.commit()                              # B: seats_left = 0, "you got it!" too
a.close()
b.close()
print("1. read-modify-write:  two students got the LAST seat. seats_left =", seats())

# ---- 2. the check INSIDE the UPDATE: atomic
reset()
a, b = SessionLocal(), SessionLocal()
take_seat = (
    update(Course)
    .where(Course.id == 1, Course.seats_left > 0)        # the check ...
    .values(seats_left=Course.seats_left - 1)            # ... and the change: ONE statement
)
result_a = a.execute(take_seat)
a.commit()
result_b = b.execute(take_seat)
b.commit()
a.close()
b.close()
print("2. atomic UPDATE:      A rowcount =", result_a.rowcount,
      "| B rowcount =", result_b.rowcount, "| seats_left =", seats())

# ---- 3. optimistic locking: version_id_col
reset()
a, b = SessionLocal(), SessionLocal()
course_a = a.get(Course, 1)                 # A reads version 1
course_b = b.get(Course, 1)                 # B reads version 1
course_a.fee = 349
a.commit()                                  # UPDATE ... WHERE id=1 AND version=1  -> version 2
course_b.fee = 399
try:
    b.commit()                              # UPDATE ... WHERE id=1 AND version=1  -> 0 rows!
except StaleDataError as exc:
    b.rollback()
    print("3. version_id_col:     B ->", type(exc).__name__)
a.close()
b.close()
with SessionLocal() as db:
    course = db.get(Course, 1)
    print("                       fee =", course.fee, "| version =", course.version)

# ---- 4. pessimistic locking: SELECT ... FOR UPDATE
stmt = select(Course).where(Course.id == 1).with_for_update()
print("4. PostgreSQL:", stmt.compile(dialect=postgresql.dialect()))
print("   SQLite:    ", stmt.compile(dialect=sqlite.dialect()))
