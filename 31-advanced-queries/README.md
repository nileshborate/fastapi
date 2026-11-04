# 31 – Advanced Queries: Joins, Group By, Having, Exists & Pagination with Totals

**FastAPI Mastery: Zero to Production** – Video 31 · Nilesh Technology

Until now we loaded whole objects. Real APIs need *answers*: the courses of one teacher, page 2 of 3,
how many students each course has, the average grade, who has no course at all. Today: SQL that
does the work **in the database** – with SQLAlchemy 2.0 `select()`.

## The project (fresh and small – Alembic + demo data)
```
31-advanced-queries/
├── alembic/versions/0001_initial.py     # teachers · courses · students · enrollments
├── app/
│   ├── seed.py                          # python -m app.seed  ->  the demo data
│   ├── schemas/   page.py (Page[T]) · course.py (CourseFilters, CourseRow) · report.py
│   ├── services/  course_service.py (search + pagination) · report_service.py
│   └── routers/   courses.py · reports.py
└── tests/         test_courses.py · test_reports.py   (13 tests)
```

## Run it
```bash
cd 31-advanced-queries
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
alembic upgrade head
python -m app.seed              # 3 teachers, 6 courses, 6 students, 11 enrollments
fastapi dev app/main.py
pytest -v                       # 13 passed (on PostgreSQL too)
```

## Endpoints
| Endpoint | The SQL idea |
|---|---|
| `GET /courses?teacher=nil&level=beginner&max_fee=250&page=2&size=2` | JOIN + filters across tables + `LIMIT/OFFSET` + a total |
| `GET /reports/courses?min_students=2` | `LEFT OUTER JOIN` + `GROUP BY` + `count` / `avg` + `HAVING` |
| `GET /reports/teachers` | two outer joins + `count(DISTINCT ...)` |
| `GET /reports/students-without-courses` | `NOT EXISTS` (`~Student.enrollments.any()`) |

## The key lines
```python
# columns from TWO tables + a filter on the other table
stmt = select(Course.id, Course.title, Teacher.name.label("teacher")).join(Course.teacher)
stmt = stmt.where(Teacher.name.icontains(f.teacher, autoescape=True))

# pagination WITH a total: count the same query, then one page
total = db.scalar(select(func.count()).select_from(stmt.subquery()))
rows = db.execute(stmt.order_by(Course.id).limit(f.size).offset((f.page - 1) * f.size)).all()

# per course: students + average grade - courses with 0 students stay (outer join)
students = func.count(Enrollment.student_id).label("students")       # NOT count(*)
select(Course.title, students, func.avg(Enrollment.grade).label("average_grade"))
    .outerjoin(Course.enrollments).group_by(Course.id, Course.title).having(students >= 2)

# students without any enrollment
select(Student).where(~Student.enrollments.any())     # WHERE NOT (EXISTS (SELECT 1 FROM enrollments ...))
```

## Three traps (all in the tests)
| Trap | What happens | Fix |
|---|---|---|
| `.join()` for a report | courses with 0 students disappear | `.outerjoin()` |
| `func.count()` = `count(*)` with an outer join | an empty course counts **1** | `func.count(Enrollment.student_id)` |
| two joins, no `distinct` | Nilesh: 7 courses, 7 students (rows multiply) | `func.count(Course.id.distinct())` |

## Interview questions
1. **What's the difference between INNER JOIN and LEFT OUTER JOIN?** An inner join keeps only rows with a match on both sides. A left outer join keeps every row of the left table; the right side is NULL when there's no match – that's how a course with 0 students stays in the report.
2. **WHERE vs HAVING?** WHERE filters rows before grouping; HAVING filters groups after GROUP BY, so it can use aggregates like `count(...) >= 2`.
3. **How do you paginate and also return the total?** Build the filtered query once; count it as a subquery (`select(func.count()).select_from(stmt.subquery())`), then apply ORDER BY + LIMIT + OFFSET for the page. Always order by something unique, or pages can overlap.

## Homework
1. `GET /students?city=Pune&page=1&size=2` – a `Page[StudentRow]` with `courses` (how many courses each student takes – a GROUP BY *inside* a paginated query).
2. `GET /reports/top-students?limit=3` – the best average grades (only graded enrollments), best first.
3. A `sort` parameter for `/courses`: `title`, `fee`, `-fee` (a whitelist – Video 25).
4. Tests for each.

Answer at the start of Video 32 (Transactions and Concurrency).
