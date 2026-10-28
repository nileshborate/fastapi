# Dependencies = small reusable functions. FastAPI calls them for us with Depends().
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status

from app.schemas.course import CourseOut
from app.services import course_service

API_KEY = "learn-fastapi-123"      # demo only - secrets move to settings in a later video


# 1. shared query parameters
def pagination(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict[str, int]:
    return {"skip": skip, "limit": limit}


# 2. a check that runs before the endpoint
def verify_api_key(x_api_key: Annotated[str, Header()]) -> None:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


# 3. load an object or stop with 404
def get_course_or_404(course_id: int) -> CourseOut:
    course = course_service.get_course(course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course


# reusable type aliases: the type + where the value comes from
Pagination = Annotated[dict[str, int], Depends(pagination)]
CourseDep = Annotated[CourseOut, Depends(get_course_or_404)]
