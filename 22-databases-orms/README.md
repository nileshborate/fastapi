# 22 – Databases and ORMs Explained

**FastAPI Mastery: Zero to Production** – Video 22 · Nilesh Technology

Our courses live in a Python dictionary – restart the server and they're gone. Real apps keep data in a **database**.
This video explains the ideas – tables, keys, SQL, SQL vs NoSQL, ORMs – with two small, runnable examples.
The next video connects FastAPI to a real database.

## What's new
```
22-databases-orms/
├── db_basics/
│   ├── sql_basics.py    # NEW: sqlite3 - CREATE TABLE, primary + foreign keys, INSERT, SELECT, JOIN, SQL injection
│   └── orm_basics.py    # NEW: SQLAlchemy 2.0 - DeclarativeBase, Mapped, mapped_column, Session, select()
├── app/                 # the app from Video 21 + homework answer
└── tests/test_db_basics.py
```

## Run it
```bash
cd 22-databases-orms
pip install -r requirements.txt     # + sqlalchemy
python -m db_basics.sql_basics      # plain SQL
python -m db_basics.orm_basics      # the ORM - echo=True prints the SQL it writes
pytest -v                           # 48 passed
```

## The words
| Word | Meaning |
|------|---------|
| Table | one kind of thing: `courses`, `students` |
| Row | one item: one course |
| Column | one property, with a type: `title TEXT`, `price REAL` |
| Primary key | a unique id for every row (`id INTEGER PRIMARY KEY`) |
| Foreign key | a column that points to a row in another table (`enrollments.course_id → courses.id`) |
| One-to-many | one teacher, many courses (a foreign key on the "many" side) |
| Many-to-many | students ↔ courses, through a link table (`enrollments`) |

## SQL vs NoSQL
| | SQL (relational) | NoSQL |
|--|--|--|
| Examples | PostgreSQL, MySQL, SQLite | MongoDB (documents), Redis (key-value) |
| Shape | tables with a fixed schema | flexible documents / keys |
| Strengths | relations, JOINs, transactions, consistency | flexible shape, simple scaling for some workloads |
| This course | **SQLite** (development) → **PostgreSQL** (production) | – |

## ORM = Object Relational Mapper
| Python | Database |
|--------|----------|
| class `Course(Base)` | table `courses` |
| attribute `title: Mapped[str]` | column `title` |
| object `Course(title=...)` | a row |
| `session.add()` + `commit()` | `INSERT` |
| `select(Course).where(Course.price < 250)` | `SELECT ... WHERE price < ?` |

**Pros:** Python instead of SQL strings, safe parameters (no SQL injection), works with many databases, type hints and editor help.
**Cons:** another thing to learn, it can hide slow queries – so look at the SQL (`echo=True`).

## SQL injection
```python
f"SELECT ... WHERE name = '{name}'"                    # NEVER - name = "x' OR '1'='1" returns every student
conn.execute("SELECT ... WHERE name = ?", (name,))     # a parameter is always just a value
```

## Interview questions
1. **What is the difference between a primary key and a foreign key?** A primary key uniquely identifies each row in its own table. A foreign key is a column that points to the primary key of a row in another table; the database rejects values that don't exist, which keeps the data consistent.
2. **SQL or NoSQL – how do you choose?** SQL databases (PostgreSQL, MySQL) store related data in tables with a fixed schema, support JOINs and transactions – the default for most business apps. NoSQL (MongoDB, Redis…) fits flexible documents, caching or special scaling needs. Many systems use both.
3. **What is an ORM, and what are its pros and cons?** An Object Relational Mapper maps classes to tables, objects to rows and attributes to columns, and writes the SQL for you (SQLAlchemy in Python). Pros: less SQL, safe parameters, portable, type hints. Cons: a learning curve and it can hide inefficient queries – check the generated SQL.

## Homework
1. `sql_basics.py`: add a `teachers` table and a `teacher_id` foreign key on `courses` (one-to-many). Write a JOIN that lists the courses of one teacher.
2. `orm_basics.py`: add a `Student` model (`id`, `name`, unique `email`); add two students and find one by email with `select()`.
3. Delete a course – with SQL (`DELETE FROM courses WHERE id = ?`) and with the ORM (`session.delete()`).
4. Tests for each.

Answer at the start of Video 23.

## Homework answer
The full code is in [23-fastapi-database/db_basics](../23-fastapi-database/db_basics) and `tests/test_db_basics.py`.
```sql
CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS courses (
    ...,
    teacher_id INTEGER REFERENCES teachers(id)       -- one teacher, many courses
);
SELECT courses.title FROM courses
JOIN teachers ON teachers.id = courses.teacher_id
WHERE teachers.name = ?;
DELETE FROM courses WHERE id = ?;
```
```python
class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)

def find_student_by_email(session: Session, email: str) -> Student | None:
    return session.scalars(select(Student).where(Student.email == email)).first()

session.delete(course)      # DELETE with the ORM
session.commit()
```
- `teachers` is created before `courses`, because `courses` points to it.
- `.first()` returns `None` when nothing matches (`.one()` would raise an error).
