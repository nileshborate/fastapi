# The reports: GROUP BY, outer joins, HAVING, NOT EXISTS
from fastapi.testclient import TestClient


def test_course_stats(client: TestClient) -> None:
    rows = client.get("/reports/courses").json()
    assert [(r["title"], r["students"]) for r in rows] == [
        ("FastAPI Basics", 4), ("Docker Deep Dive", 2), ("Python 101", 2),
        ("SQL for Beginners", 2), ("System Design", 1), ("React Basics", 0),
    ]
    assert rows[0] == {"title": "FastAPI Basics", "teacher": "Nilesh", "students": 4,
                       "average_grade": 88.25}


def test_outer_join_keeps_empty_courses(client: TestClient) -> None:
    react = client.get("/reports/courses").json()[-1]
    assert react == {"title": "React Basics", "teacher": "Priya", "students": 0,
                     "average_grade": None}        # count(column) = 0, not 1 like count(*)


def test_average_ignores_missing_grades(client: TestClient) -> None:
    rows = {r["title"]: r for r in client.get("/reports/courses").json()}
    assert rows["Python 101"]["average_grade"] == 78.0     # Asha 78 + Ravi (no grade yet)
    assert rows["System Design"]["average_grade"] is None


def test_having_min_students(client: TestClient) -> None:
    rows = client.get("/reports/courses", params={"min_students": 2}).json()
    assert [r["title"] for r in rows] == ["FastAPI Basics", "Docker Deep Dive", "Python 101",
                                          "SQL for Beginners"]


def test_teacher_stats_count_distinct(client: TestClient) -> None:
    assert client.get("/reports/teachers").json() == [
        {"teacher": "Nilesh", "courses": 3, "students": 5},
        {"teacher": "Priya", "courses": 3, "students": 3},
        {"teacher": "Arjun", "courses": 0, "students": 0},
    ]


def test_students_without_courses(client: TestClient) -> None:
    assert client.get("/reports/students-without-courses").json() == [
        {"id": 6, "name": "Dev", "city": "Pune"}
    ]
