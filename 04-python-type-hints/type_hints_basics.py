# Video 4 - Python Type Hints: all the examples from the video
# Run:  python type_hints_basics.py
#       mypy type_hints_basics.py      (should report: Success)

from typing import Annotated, Optional

# --- Basic types --------------------------------------------------------
age: int = 25
price: float = 499.5
name: str = "Nilesh"
is_active: bool = True


def greet(name: str, times: int) -> str:
    return ("Hello, " + name + "! ") * times


def log(message: str) -> None:          # returns nothing
    print(message)


# --- Union and Optional -------------------------------------------------
def describe(value: int | str) -> str:  # int OR str (Python 3.10+)
    return f"{value!r} is a {type(value).__name__}"


def final_price(price: float, discount: float | None = None) -> float:
    if discount is None:
        return price
    return price - discount


def final_price_old_style(price: float, discount: Optional[float] = None) -> float:
    # Optional[float] is exactly the same as float | None
    return price if discount is None else price - discount


# --- Collections --------------------------------------------------------
tags: list[str] = ["python", "api"]
marks: dict[str, int] = {"maths": 90, "science": 85}
location: tuple[float, float] = (18.6298, 73.7997)   # latitude, longitude
unique_ids: set[int] = {1, 2, 3}
students: list[dict[str, int]] = [{"id": 1, "age": 20}, {"id": 2, "age": 22}]


def add_tag(tag: str, existing: list[str] | None = None) -> list[str]:
    # Don't use a mutable default like  existing: list[str] = []
    if existing is None:
        existing = []
    existing.append(tag)
    return existing


# --- Classes and type aliases -------------------------------------------
CourseId = int                       # type alias


class Course:
    def __init__(self, course_id: CourseId, title: str) -> None:
        self.course_id = course_id
        self.title = title


class Student:
    def __init__(self, name: str) -> None:
        self.name = name


def enrol(student: Student, course: Course) -> str:
    return f"{student.name} enrolled in {course.title}"


# --- Annotated ------------------------------------------------------------
Percentage = Annotated[int, "must be between 0 and 100"]   # still just an int


def set_progress(value: Percentage) -> str:
    return f"Progress: {value}%"


if __name__ == "__main__":
    print(greet("Nilesh", 2))
    print(describe(7), "|", describe("seven"))
    print(final_price(999.0, 100.0), final_price(999.0))
    print(add_tag("fastapi"), add_tag("python"))   # two separate lists
    print(enrol(Student("Asha"), Course(7, "FastAPI Mastery")))
    print(set_progress(75))
