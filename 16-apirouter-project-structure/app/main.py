# Video 16 - APIRouter and Project Structure
# Run (from the 16-apirouter-project-structure folder):  fastapi dev app/main.py
from fastapi import FastAPI

from app.routers import courses, students

app = FastAPI(title="Course Hub API", version="2.0.0")

app.include_router(courses.router)
app.include_router(students.router)


@app.get("/", tags=["Health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
