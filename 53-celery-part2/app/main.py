# Video 53 - Background jobs with Celery, Part 2: retries, schedules, workflows, monitoring
# Redis:  docker run -d --name redis -p 6379:6379 redis:7-alpine
# Worker: celery -A app.celery_app worker --loglevel=info --pool=threads --concurrency=4
# Beat:   celery -A app.celery_app beat --loglevel=info
# Flower: celery -A app.celery_app flower           -> http://localhost:5555
# API:    fastapi dev app/main.py
from fastapi import FastAPI

from app.routers import jobs, workers

app = FastAPI(title="Course Hub Jobs 2", version="1.0.0")
app.include_router(jobs.router)
app.include_router(workers.router)
