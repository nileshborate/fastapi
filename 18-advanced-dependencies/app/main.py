# Video 18 - Advanced Dependencies
# Run (from the 18-advanced-dependencies folder):  fastapi dev app/main.py
from fastapi import FastAPI

from app.routers import admin, courses, students, teachers

app = FastAPI(title="Course Hub API", version="2.2.0")

app.include_router(courses.router)
app.include_router(students.router)
app.include_router(teachers.router)
app.include_router(admin.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
