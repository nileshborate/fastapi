# Video 4 - Python Type Hints for FastAPI
# Nilesh Technology - FastAPI Mastery: Zero to Production
#
# Run:   fastapi dev main.py
# Try:   http://127.0.0.1:8000/courses/7
#        http://127.0.0.1:8000/courses/7?level=beginner
#        http://127.0.0.1:8000/courses/0      (422 - must be greater than 0)
#        http://127.0.0.1:8000/courses/abc    (422 - not an integer)
#        http://127.0.0.1:8000/docs

from typing import Annotated

from fastapi import FastAPI, Path

app = FastAPI()


@app.get("/courses/{course_id}")
def get_course(
    course_id: Annotated[int, Path(gt=0)],   # int, from the path, must be > 0
    level: str | None = None,                # optional query parameter
) -> dict[str, int | str | None]:
    return {"course_id": course_id, "level": level}
