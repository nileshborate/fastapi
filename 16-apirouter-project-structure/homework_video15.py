# Homework answer from Video 15 - cookies, headers, form + PDF upload
# Run:  fastapi dev homework_video15.py
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Cookie, FastAPI, Form, Header, HTTPException, Response, UploadFile, status

app = FastAPI(title="Courses - Homework 15")

API_KEY = "learn-fastapi-123"
UPLOAD_DIR = Path("uploads")
MAX_PDF_SIZE = 5_000_000            # 5 MB
COURSES = {1: {"id": 1, "title": "FastAPI Basics"}, 2: {"id": 2, "title": "Pydantic Models"}}


@app.get("/courses/{course_id}")
def get_course(course_id: int, response: Response) -> dict[str, Any]:
    if course_id not in COURSES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    response.set_cookie(key="last_viewed", value=str(course_id), max_age=24 * 60 * 60, httponly=True, samesite="lax")
    return COURSES[course_id]


@app.get("/recent")
def recent(last_viewed: Annotated[int | None, Cookie()] = None) -> dict[str, Any]:
    if last_viewed is None or last_viewed not in COURSES:
        return {"message": "Nothing viewed yet"}
    return COURSES[last_viewed]


@app.post("/courses/{course_id}/resources", status_code=status.HTTP_201_CREATED)
async def upload_resource(
    course_id: int,
    x_api_key: Annotated[str, Header()],
    title: Annotated[str, Form(min_length=3)],
    file: UploadFile,
) -> dict[str, Any]:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only PDF files are allowed")
    content = await file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="PDF is larger than 5 MB")
    UPLOAD_DIR.mkdir(exist_ok=True)
    saved_as = f"{uuid4().hex}.pdf"
    (UPLOAD_DIR / saved_as).write_bytes(content)
    return {"course_id": course_id, "title": title, "saved_as": saved_as, "size": len(content)}
