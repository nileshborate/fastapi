# Homework answer (Video 31)
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Row
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.page import Page
from app.schemas.student import StudentFilters, StudentRow, TopStudent
from app.services import student_service

router = APIRouter(tags=["Students"])


@router.get("/students", response_model=Page[StudentRow])
def search_students(
    filters: Annotated[StudentFilters, Query()],
    db: Session = Depends(get_db),
) -> Page:
    return student_service.search_students(db, filters)


@router.get("/reports/top-students", response_model=list[TopStudent])
def top_students(
    limit: int = Query(default=3, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[Row]:
    return student_service.top_students(db, limit)
