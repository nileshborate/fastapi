# Video 17 - Dependency Injection Basics
# Run (from the 17-dependency-injection folder):  fastapi dev app/main.py
from fastapi import FastAPI

from app.routers import courses, students, teachers

app = FastAPI(title="Course Hub API", version="2.1.0")

app.include_router(courses.router)
app.include_router(students.router)
app.include_router(teachers.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
