# Video 52 - Background jobs with Celery, Part 1
# Redis:  docker run -d --name redis -p 6379:6379 redis:7-alpine
# Worker: celery -A app.celery_app worker --loglevel=info --pool=solo   (solo: works on Windows)
# API:    fastapi dev app/main.py
from fastapi import FastAPI

from app.routers import reports, tasks, users

app = FastAPI(title="Course Hub Jobs", version="1.0.0")
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(tasks.router)
