# 30 – The Association Object: a Link with Its Own Data

**FastAPI Mastery: Zero to Production** – Video 30 · Nilesh Technology

In Video 27 the link table had only two columns: `student_id` and `course_id`. But real links have data:
**when** did the student enroll? Which **grade** did they get? Then the link becomes a class of its own – the **association object**.

## The project (fresh and small – with Alembic from Videos 28–29)
```
30-association-object/
├── alembic/versions/
│   ├── 0001_students_courses_enrollments.py   # the plain link table (like Video 27)
│   └── 0002_enrollment_data.py                # + enrolled_at, grade  (the old links survive)
├── app/
│   ├── models/    student.py · course.py · enrollment.py  (class Enrollment)
│   ├── schemas/   enrollment.py  (EnrollmentOut · RosterRow · StudentDetail · CourseDetail)
│   ├── services/  student_service.py (enroll · set_grade · unenroll) · course_service.py
│   └── routers/   students.py · courses.py
└── tests/         test_enrollments.py · test_migrations.py   (13 tests)
```

## Run it
```bash
cd 30-association-object
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
alembic upgrade head
fastapi dev app/main.py
pytest -v                       # 13 passed (on PostgreSQL too)
```

## The association object
```python
class Enrollment(Base):
    __tablename__ = "enrollments"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)

    enrolled_at: Mapped[datetime] = mapped_column(server_default=func.now())   # the DATABASE fills it
    grade: Mapped[int | None]                                                  # set later

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course: Mapped["Course"] = relationship(back_populates="enrollments")
```
Many-to-many = **two one-to-many** relationships through `Enrollment`:
```python
# Student
enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student", cascade="all, delete-orphan")
courses: AssociationProxy[list["Course"]] = association_proxy("enrollments", "course")   # a shortcut

# Course
enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course", cascade="all, delete-orphan")
average_grade: Mapped[float | None] = column_property(
    select(func.avg(Enrollment.grade)).where(Enrollment.course_id == id).correlate_except(Enrollment).scalar_subquery())
```

## Endpoints
| Method | Path | |
|---|---|---|
| POST | `/students/{student_id}/enrollments` `{"course_id": 1}` | 201 – `course`, `enrolled_at`, `grade: null` · 409 Already enrolled · 404 |
| PATCH | `/students/{student_id}/enrollments/{course_id}` `{"grade": 92}` | 200 · 422 (0–100) · 404 Enrollment not found |
| DELETE | `/students/{student_id}/enrollments/{course_id}` | 204 · 404 |
| GET | `/students/{student_id}` | the student + enrollments (course, enrolled_at, grade) – **3 queries** |
| GET | `/courses/{course_id}` | the course + `average_grade` + the roster |
| GET | `/students/{student_id}/courses` | the association proxy |

```python
db.get(Enrollment, (student_id, course_id))          # a composite primary key -> a tuple
select(Student).options(selectinload(Student.enrollments).selectinload(Enrollment.course))   # chained loading
```

## Interview questions
1. **When do you use an association object instead of a plain link table (`secondary=`)?** When the link itself has data – a date, a grade, a role, a quantity. The link becomes a mapped class with its own columns; many-to-many becomes two one-to-many relationships.
2. **What does `association_proxy` do?** It's a shortcut across the association object: `student.courses` reads `enrollment.course` for every enrollment – you don't have to write the loop.
3. **How do you load a student, their enrollments AND each course without the N+1 problem?** Chain the loaders: `selectinload(Student.enrollments).selectinload(Enrollment.course)` – 3 queries, however many courses.

## Homework
1. A `status` column on Enrollment: `"active"` / `"completed"` / `"dropped"` – a migration with `server_default="active"` (old rows!), and a PATCH that can change it.
2. `GET /courses/{course_id}?status=active` – only those students in the roster.
3. A `completed_count` on CourseOut (a `column_property` counting the completed enrollments).
4. Tests for each.

Answer at the start of Video 31 (Advanced Queries).
