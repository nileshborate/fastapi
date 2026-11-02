# 26 – Relationships: One Teacher, Many Courses

**FastAPI Mastery: Zero to Production** – Video 26 · Nilesh Technology

A **fresh, small project** – only what this topic needs. (Everything from Videos 1–25 is still in its own folder.)
One teacher teaches many courses: a **foreign key**, `relationship()` with `back_populates`, nested response schemas,
the **N+1 problem** and `selectinload`, and what to do when a teacher who still has courses is deleted.

## The project
```
26-relationships/
├── app/
│   ├── config.py · database.py     # + PRAGMA foreign_keys=ON for SQLite
│   ├── errors.py                   # NotFoundError -> 404 · ConflictError -> 409
│   ├── models/   teacher.py · course.py      # ForeignKey + relationship(back_populates=...)
│   ├── schemas/  teacher.py · course.py      # nested: CourseOut.teacher · TeacherDetail.courses
│   ├── services/ teacher_service.py · course_service.py
│   ├── routers/  teachers.py · courses.py
│   ├── dependencies.py · main.py
├── demos/n_plus_one.py             # python -m demos.n_plus_one
└── tests/                          # 16 tests + test_homework26.py
```

## Run it
```bash
cd 26-relationships
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
fastapi dev app/main.py
python -m demos.n_plus_one      # lazy: 6 queries · selectinload: 2 queries
pytest -v                       # 21 passed: 16 + 5 homework-answer tests (on PostgreSQL too)
```

## The models
```python
class Teacher(Base):
    courses: Mapped[list["Course"]] = relationship(back_populates="teacher", order_by="Course.id")

class Course(Base):
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))   # a real column
    teacher: Mapped["Teacher"] = relationship(back_populates="courses")  # a Python link, not a column
```
`FOREIGN KEY(teacher_id) REFERENCES teachers (id)` – and on SQLite only with `PRAGMA foreign_keys=ON`.

## N+1 and selectinload
```python
select(Course).options(selectinload(Course.teacher))
# SELECT ... FROM courses ORDER BY courses.id
# SELECT ... FROM teachers WHERE teachers.id IN (?, ?)
```

## Interview questions
1. **What is the N+1 query problem, and how do you fix it in SQLAlchemy?** One query loads N rows, then touching a relationship on each row runs one more query per row: N+1. Fix it with eager loading: `selectinload` (a second query with `IN (...)`) or `joinedload` (a JOIN in the same query).
2. **What does `back_populates` do?** It links the two sides of one relationship (`Teacher.courses` ↔ `Course.teacher`), so changing one side updates the other in Python too.
3. **What happens when you delete a parent that still has children?** You decide: block it (409 / `RESTRICT`), delete the children too (`cascade="all, delete-orphan"` / `ON DELETE CASCADE`), or set the foreign key to NULL. Without a decision, SQLAlchemy tries to set `teacher_id` to NULL – and a NOT NULL column fails.

## Homework
1. `PATCH /courses/{course_id}` that can move a course to another teacher (`teacher_id`) – 404 if that teacher doesn't exist.
2. `GET /teachers?with_courses=true` – return `TeacherDetail` for every teacher, with `selectinload(Teacher.courses)` (only 2 queries – test it!).
3. A `course_count` field in `TeacherOut`.
4. Tests for each.

Answer at the start of Video 27.

## Homework answer
Shown at the start of Video 27. The code is in THIS folder (`schemas/course.py`, `services/course_service.py`, `routers/courses.py`,
`services/teacher_service.py`, `routers/teachers.py`, `models/teacher.py`, `tests/test_homework26.py`).
```python
# 1. PATCH /courses/{course_id} - move a course to another teacher
class CourseUpdate(BaseModel):          # title · price · teacher_id - all optional, null not allowed
    ...
if "teacher_id" in changes and db.get(Teacher, changes["teacher_id"]) is None:
    raise NotFoundError("Teacher")      # 404 before we change anything

# 2. GET /teachers?with_courses=true - 2 queries, tested with before_cursor_execute
if with_courses:
    query = query.options(selectinload(Teacher.courses))
return [TeacherDetail.model_validate(t) for t in teachers]       # else: TeacherOut - 1 query

# 3. course_count - counted INSIDE the same SELECT (column_property + a scalar subquery)
course_count: Mapped[int] = column_property(
    select(func.count(Course.id)).where(Course.teacher_id == id).correlate_except(Course).scalar_subquery()
)
# SELECT (SELECT count(courses.id) FROM courses WHERE courses.teacher_id = teachers.id) AS anon_1, teachers.id, ...
```
Why not `len(teacher.courses)`? That loads every course of every teacher – the N+1 problem again.
