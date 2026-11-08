# Run: python -m demos.sqlmodel_demo   - SQLModel: ONE class = a table AND a Pydantic schema
from pydantic import ValidationError
from sqlmodel import Field, Session, SQLModel, create_engine, select


class CourseBase(SQLModel):                 # the shared fields
    title: str = Field(min_length=3, max_length=100)
    fee: int = Field(ge=0)


class Course(CourseBase, table=True):       # table=True: a database TABLE
    id: int | None = Field(default=None, primary_key=True)


class CourseCreate(CourseBase):             # no table=True: only a SCHEMA (validates)
    pass


engine = create_engine("sqlite://")         # an in-memory database, just for the demo
SQLModel.metadata.create_all(engine)

with Session(engine) as db:
    course = Course.model_validate(CourseCreate(title="FastAPI Basics", fee=299))
    db.add(course)
    db.commit()
    db.refresh(course)
    print("1. saved:", course)
    print("2. query:", db.exec(select(Course).where(Course.fee > 100)).all())

try:
    CourseCreate(title="FastAPI Basics", fee=-5)
except ValidationError as error:
    print("3. schema: ValidationError -", error.errors()[0]["msg"])
print("4. table: no check!", Course(title="FastAPI Basics", fee=-5))
