# Answer to the Video 7 homework: /contact and async /stats
from fastapi import FastAPI

app = FastAPI(title="Course Hub API", version="1.0.0")

COURSES: list[dict[str, str | int]] = [
    {"id": 1, "title": "FastAPI Basics", "level": "beginner"},
    {"id": 2, "title": "Pydantic Models", "level": "beginner"},
    {"id": 3, "title": "Databases with SQLAlchemy", "level": "intermediate"},
]


@app.get("/contact")
def contact() -> dict[str, str]:
    return {"email": "nileshhanumantborate@gmail.com", "website": "https://www.nileshtechnology.in"}


@app.get("/stats")
async def stats() -> dict[str, int]:
    return {"total_courses": len(COURSES)}
