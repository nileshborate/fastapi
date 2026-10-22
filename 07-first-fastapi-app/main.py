# Video 7 - Your First FastAPI App
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000   and   /docs
from fastapi import FastAPI

# 1. Create the application object
app = FastAPI(
    title="Course Hub API",
    description="My first FastAPI app - Nilesh Technology",
    version="1.0.0",
)

# Sample data (a real database comes later in the course)
COURSES: list[dict[str, str | int]] = [
    {"id": 1, "title": "FastAPI Basics", "level": "beginner"},
    {"id": 2, "title": "Pydantic Models", "level": "beginner"},
    {"id": 3, "title": "Databases with SQLAlchemy", "level": "intermediate"},
]


# 2. First route: GET /
@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Welcome to Course Hub API"}


# 3. More routes
@app.get("/about")
def about() -> dict[str, str]:
    return {"course": "FastAPI Mastery", "channel": "Nilesh Technology"}


@app.get("/courses")
def list_courses() -> list[dict[str, str | int]]:
    return COURSES


# 4. An async route (from Video 5)
@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# 5. Optional: run with  python main.py
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
