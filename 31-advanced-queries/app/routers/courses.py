from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.course import CourseFilters, CourseRow
from app.schemas.page import Page
from app.services import course_service

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("", response_model=Page[CourseRow])
def search_courses(
    filters: Annotated[CourseFilters, Query()],
    db: Session = Depends(get_db),
) -> Page:
    return course_service.search_courses(db, filters)
