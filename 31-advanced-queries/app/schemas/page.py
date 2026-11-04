# One response shape for every paginated list: the items + the numbers around them
from pydantic import BaseModel


class Page[T](BaseModel):           # a GENERIC model: Page[CourseRow], Page[StudentOut], ...
    items: list[T]
    total: int                      # how many rows match - on ALL pages
    page: int
    size: int
    pages: int
