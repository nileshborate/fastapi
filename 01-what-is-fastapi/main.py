# Video 1 - What is FastAPI and Why Learn It?
# Nilesh Technology - FastAPI Mastery: Zero to Production
#
# Run:   fastapi dev main.py
# Open:  http://127.0.0.1:8000/courses/7
#        http://127.0.0.1:8000/courses/abc   (see the automatic validation error)
#        http://127.0.0.1:8000/docs          (interactive documentation)

from fastapi import FastAPI

app = FastAPI()


@app.get("/courses/{course_id}")
def get_course(course_id: int):
    return {"id": course_id, "title": "FastAPI Mastery"}
