# 27 – Many-to-Many: Students and Courses

**FastAPI Mastery: Zero to Production** – Video 27 · Nilesh Technology

A **fresh, small project**. A student takes many courses, and a course has many students.
The answer: a **link table** (`enrollments`) with two foreign keys, and `relationship(secondary=...)` on both sides.

## The project
```
27-many-to-many/
├── app/
│   ├── models/   enrollment.py (the link Table) · student.py · course.py
│   ├── schemas/  student.py · course.py · details.py (StudentDetail · CourseDetail)
│   ├── services/ student_service.py (enroll · unenroll) · course_service.py
│   ├── routers/  students.py · courses.py
│   ├── config.py · database.py (PRAGMA foreign_keys=ON) · errors.py · dependencies.py · main.py
└── tests/        test_basics.py · test_enrollments.py · test_link_table.py   (15 tests)
```

## Run it
```bash
cd 27-many-to-many
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
fastapi dev app/main.py
pytest -v                       # 19 passed: 15 + 4 homework-answer tests (on PostgreSQL too)
```

## The link table
```python
enrollments = Table(
    "enrollments", Base.metadata,
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    Column("course_id", ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
)
class Student(Base):
    courses: Mapped[list["Course"]] = relationship(secondary=enrollments, back_populates="students")
class Course(Base):
    students: Mapped[list["Student"]] = relationship(secondary=enrollments, back_populates="courses")
```
| Python | SQL |
|---|---|
| `student.courses.append(course)` | `INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)` |
| `student.courses.remove(course)` | `DELETE FROM enrollments WHERE student_id = ? AND course_id = ?` |
| `db.delete(student)` | the student's enrollments first, then `DELETE FROM students` |

## Endpoints
`POST /students/{student_id}/courses/{course_id}` → 201 (409 "Already enrolled") ·
`DELETE /students/{student_id}/courses/{course_id}` → 204 (404 "Enrollment not found") ·
`GET /students/{id}` (+ courses) · `GET /courses/{id}` (+ students)

## Interview questions
1. **How do you model a many-to-many relationship in a relational database?** With a link (association) table that has two foreign keys, one to each table. A composite primary key on both columns stops the same pair from being saved twice. In SQLAlchemy: `relationship(secondary=link_table)` on both sides.
2. **When do you need an association object instead of a plain link table?** When the link itself has data – like `enrolled_at` or a grade. Then the link becomes a model class (`Enrollment`) with its own columns, and two one-to-many relationships.
3. **What's the difference between `ondelete="CASCADE"` and SQLAlchemy's cascade?** `ondelete` is part of the table: the DATABASE deletes the rows, for every tool. SQLAlchemy's cascade happens in Python, in the session – it only works when you delete through the ORM.

## Homework
1. A `max_students` column on Course (default 30) – enrolling in a full course → **409** "Course is full".
2. `GET /students/{student_id}/courses` – the student's courses as a list.
3. A `student_count` field in CourseOut (a `column_property`, like the homework answer of Video 26).
4. Tests for each.

Answer at the start of Video 28.

## Homework answer
Shown at the start of Video 28. The code is in THIS folder (`models/course.py`, `schemas/course.py`,
`services/student_service.py`, `routers/students.py`, `tests/test_homework27.py`).
```python
# 1. max_students - a full course -> 409
max_students: Mapped[int] = mapped_column(default=30)                 # model
max_students: int = Field(default=30, ge=1)                            # CourseCreate
if len(course.students) >= course.max_students:                        # enroll()
    raise ConflictError("Course is full")

# 2. GET /students/{student_id}/courses
@router.get("/{student_id}/courses", response_model=list[CourseOut])
def list_student_courses(student: StudentDep) -> list[Course]:
    return student.courses

# 3. student_count - counted in the same SELECT, straight from the link table
student_count: Mapped[int] = column_property(
    select(func.count()).where(enrollments.c.course_id == id).correlate_except(enrollments).scalar_subquery()
)
# enroll() calls db.refresh(course) after the commit, so the answer shows the NEW count
```
