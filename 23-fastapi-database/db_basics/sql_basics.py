# Part 1: plain SQL with Python's built-in sqlite3 module - no ORM yet.
# Run (from the 22-databases-orms folder):  python -m db_basics.sql_basics
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS teachers (        -- homework (Video 22)
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS courses (
    id    INTEGER PRIMARY KEY,               -- primary key: a unique id for every row
    title TEXT    NOT NULL UNIQUE,
    price REAL    NOT NULL CHECK (price >= 0),
    teacher_id INTEGER REFERENCES teachers(id)               -- one teacher, many courses
);
CREATE TABLE IF NOT EXISTS students (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS enrollments (     -- connects students and courses
    student_id INTEGER NOT NULL REFERENCES students(id),   -- foreign key
    course_id  INTEGER NOT NULL REFERENCES courses(id),    -- foreign key
    PRIMARY KEY (student_id, course_id)
);
"""


def connect(path: str = "school.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")     # SQLite checks foreign keys only when you ask
    conn.executescript(SCHEMA)
    return conn


def add_teacher(conn: sqlite3.Connection, name: str) -> int:              # homework (Video 22)
    cur = conn.execute("INSERT INTO teachers (name) VALUES (?)", (name,))
    conn.commit()
    return cur.lastrowid or 0


def add_course(
    conn: sqlite3.Connection, title: str, price: float, teacher_id: int | None = None
) -> int:
    cur = conn.execute(
        "INSERT INTO courses (title, price, teacher_id) VALUES (?, ?, ?)", (title, price, teacher_id)
    )
    conn.commit()                                # save it for real
    return cur.lastrowid or 0


def add_student(conn: sqlite3.Connection, name: str, email: str) -> int:
    cur = conn.execute("INSERT INTO students (name, email) VALUES (?, ?)", (name, email))
    conn.commit()
    return cur.lastrowid or 0


def enroll(conn: sqlite3.Connection, student_id: int, course_id: int) -> None:
    conn.execute(
        "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id)
    )
    conn.commit()


def courses_of(conn: sqlite3.Connection, student_name: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT courses.title
        FROM courses
        JOIN enrollments ON enrollments.course_id = courses.id
        JOIN students    ON students.id = enrollments.student_id
        WHERE students.name = ?
        ORDER BY courses.title
        """,
        (student_name,),
    ).fetchall()
    return [row[0] for row in rows]


def courses_of_teacher(conn: sqlite3.Connection, teacher_name: str) -> list[str]:  # homework
    rows = conn.execute(
        """
        SELECT courses.title
        FROM courses
        JOIN teachers ON teachers.id = courses.teacher_id
        WHERE teachers.name = ?
        ORDER BY courses.title
        """,
        (teacher_name,),
    ).fetchall()
    return [row[0] for row in rows]


def delete_course(conn: sqlite3.Connection, course_id: int) -> None:      # homework (Video 22)
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()


def find_student_unsafe(conn: sqlite3.Connection, name: str) -> list[tuple[str, str]]:
    sql = f"SELECT name, email FROM students WHERE name = '{name}'"      # NEVER do this!
    return conn.execute(sql).fetchall()


def find_student_safe(conn: sqlite3.Connection, name: str) -> list[tuple[str, str]]:
    return conn.execute("SELECT name, email FROM students WHERE name = ?", (name,)).fetchall()


def main() -> None:
    Path("school.db").unlink(missing_ok=True)    # start fresh every run
    conn = connect("school.db")
    fastapi = add_course(conn, "FastAPI Basics", 299)
    pydantic = add_course(conn, "Pydantic Models", 199)
    add_course(conn, "Async Python", 249)
    asha = add_student(conn, "Asha", "asha@example.com")
    add_student(conn, "Ravi", "ravi@example.com")
    enroll(conn, asha, fastapi)
    enroll(conn, asha, pydantic)

    print("All courses:", conn.execute("SELECT id, title, price FROM courses").fetchall())
    print("Under 250:  ", conn.execute("SELECT title FROM courses WHERE price < 250").fetchall())
    print("Asha takes: ", courses_of(conn, "Asha"))

    try:
        enroll(conn, asha, 99)                   # course 99 does not exist
    except sqlite3.IntegrityError as error:
        print("Blocked:    ", error)

    attack = "x' OR '1'='1"
    print("Unsafe:     ", find_student_unsafe(conn, attack))    # every student!
    print("Safe:       ", find_student_safe(conn, attack))      # nobody
    conn.close()


if __name__ == "__main__":
    main()
