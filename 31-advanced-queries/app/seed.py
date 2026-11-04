# Demo data for the queries - run once:  python -m app.seed
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Course, Enrollment, Student, Teacher

TEACHERS = ["Nilesh", "Priya", "Arjun"]                     # Arjun has no courses (yet)

COURSES = [  # title, level, fee, teacher
    ("FastAPI Basics", "beginner", 299, "Nilesh"),
    ("Docker Deep Dive", "advanced", 499, "Nilesh"),
    ("System Design", "advanced", 999, "Nilesh"),
    ("Python 101", "beginner", 99, "Priya"),
    ("SQL for Beginners", "beginner", 199, "Priya"),
    ("React Basics", "intermediate", 399, "Priya"),          # no students
]

STUDENTS = [("Asha", "Pune"), ("Ravi", "Mumbai"), ("Meera", "Pune"),
            ("Kabir", "Delhi"), ("Sara", "Mumbai"), ("Dev", "Pune")]   # Dev: no courses

ENROLLMENTS = [  # student, course, grade (None = not graded yet)
    ("Asha", "FastAPI Basics", 92), ("Asha", "Docker Deep Dive", 85),
    ("Asha", "Python 101", 78),
    ("Ravi", "FastAPI Basics", 78), ("Ravi", "Python 101", None),
    ("Ravi", "SQL for Beginners", 66),
    ("Meera", "FastAPI Basics", 88), ("Meera", "System Design", None),
    ("Kabir", "Docker Deep Dive", 75), ("Kabir", "SQL for Beginners", 84),
    ("Sara", "FastAPI Basics", 95),
]


def seed(db: Session) -> None:
    teachers = {name: Teacher(name=name) for name in TEACHERS}
    courses = {title: Course(title=title, level=level, fee=fee, teacher=teachers[teacher])
               for title, level, fee, teacher in COURSES}
    students = {name: Student(name=name, city=city) for name, city in STUDENTS}
    db.add_all([*teachers.values(), *courses.values(), *students.values()])
    db.add_all(
        Enrollment(student=students[s], course=courses[c], grade=g) for s, c, g in ENROLLMENTS
    )
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("seeded: 3 teachers, 6 courses, 6 students, 11 enrollments")
