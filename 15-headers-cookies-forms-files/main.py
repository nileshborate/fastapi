# Video 15 - Headers, Cookies, Forms and File Uploads
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import uuid4

from fastapi import Cookie, FastAPI, File, Form, Header, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Course Hub API", version="1.8.0")

API_KEY = "learn-fastapi-123"              # demo only - real secrets come from settings (later video)
UPLOAD_DIR = Path("uploads")
MAX_IMAGE_SIZE = 1_000_000                 # 1 MB
IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg"}

COURSES = [{"id": 1, "title": "FastAPI Basics"}, {"id": 2, "title": "Pydantic Models"}]


# ---------------------------------------------------------------- 1. headers
@app.get("/whoami")
def whoami(
    user_agent: Annotated[str | None, Header()] = None,
    accept_language: Annotated[str | None, Header()] = None,
) -> dict[str, str | None]:
    # user_agent  -> reads the "User-Agent" header
    return {"user_agent": user_agent, "accept_language": accept_language}


@app.get("/reports")
def reports(x_api_key: Annotated[str, Header()]) -> dict[str, Any]:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return {"total_courses": len(COURSES), "total_students": 42}


@app.get("/courses")
def list_courses(response: Response) -> list[dict[str, Any]]:
    response.headers["Cache-Control"] = "public, max-age=60"   # a response header
    return COURSES


# ---------------------------------------------------------------- 2. cookies
@app.post("/preferences/theme")
def set_theme(theme: Literal["light", "dark"], response: Response) -> dict[str, str]:
    response.set_cookie(
        key="theme",
        value=theme,
        max_age=30 * 24 * 60 * 60,   # 30 days, in seconds
        httponly=True,               # JavaScript in the page can't read it
        samesite="lax",
    )
    return {"message": f"Theme set to {theme}"}


@app.get("/preferences")
def get_preferences(theme: Annotated[str, Cookie()] = "light") -> dict[str, str]:
    return {"theme": theme}


@app.delete("/preferences/theme")
def reset_theme(response: Response) -> dict[str, str]:
    response.delete_cookie("theme")
    return {"message": "Theme reset"}


# ---------------------------------------------------------------- 3. forms
@app.post("/login")
def login(
    username: Annotated[str, Form(min_length=3)],
    password: Annotated[str, Form(min_length=8)],
) -> dict[str, str]:
    # demo only - real login with hashed passwords and tokens comes in the security videos
    return {"message": f"Welcome, {username}!"}


class ContactForm(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    message: str = Field(min_length=10, max_length=500)


@app.post("/contact")
def contact(form: Annotated[ContactForm, Form()]) -> dict[str, str]:
    return {"message": f"Thanks {form.name}, we will reply to {form.email}"}


# ---------------------------------------------------------------- 4. file uploads
@app.post("/files/size")
def file_size(file: Annotated[bytes, File()]) -> dict[str, int]:
    # bytes: the WHOLE file is read into memory - fine for small files only
    return {"size": len(file)}


@app.post("/courses/{course_id}/thumbnail", status_code=status.HTTP_201_CREATED)
async def upload_thumbnail(
    course_id: int,
    file: UploadFile,
    alt_text: Annotated[str, Form(max_length=100)] = "",
) -> dict[str, Any]:
    # 1. check the type
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PNG or JPEG images are allowed",
        )
    # 2. check the size
    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image is larger than 1 MB",
        )
    # 3. save it with a SAFE name we create ourselves
    UPLOAD_DIR.mkdir(exist_ok=True)
    saved_as = f"{uuid4().hex}{IMAGE_TYPES[file.content_type]}"
    (UPLOAD_DIR / saved_as).write_bytes(content)
    return {
        "course_id": course_id,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "saved_as": saved_as,
        "alt_text": alt_text,
    }


@app.post("/materials")
async def upload_materials(files: list[UploadFile]) -> list[dict[str, Any]]:
    result = []
    for f in files:
        content = await f.read()
        result.append({"name": f.filename, "size": len(content)})
    return result
