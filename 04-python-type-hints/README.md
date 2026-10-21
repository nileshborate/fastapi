# Video 4 – Python Type Hints for FastAPI

Type hints are labels that say what type a variable, parameter or return value should be. **Python doesn't enforce them at runtime** – editors, `mypy`, Pydantic and FastAPI use them.

## Files
| File | What it shows |
|------|---------------|
| `type_hints_basics.py` | Every example from the video: basic types, unions, collections, classes, aliases, `Annotated` |
| `mypy_demo.py` | A deliberate mistake that `mypy` catches before you run |
| `main.py` | How FastAPI uses type hints: conversion, validation, docs |
| `homework.py` | Add type hints, then pass `mypy --strict` |

## Run
```bash
pip install -r requirements.txt
python type_hints_basics.py
mypy mypy_demo.py            # shows the error
fastapi dev main.py          # then open the URLs below
```
| URL | Result |
|-----|--------|
| `/courses/7` | `{"course_id": 7, "level": null}` |
| `/courses/7?level=beginner` | `{"course_id": 7, "level": "beginner"}` |
| `/courses/0` | 422 – *Input should be greater than 0* |
| `/courses/abc` | 422 – not a valid integer |
| `/docs` | `course_id` shown as integer, `level` as optional string |

## Cheat sheet
| Type hint | Meaning |
|-----------|---------|
| `int`, `float`, `str`, `bool` | Basic types |
| `-> None` | Function returns nothing |
| `int \| str` | int **or** str (Python 3.10+) |
| `float \| None = None` / `Optional[float] = None` | May be None, default None |
| `list[str]`, `dict[str, int]`, `tuple[float, float]`, `set[int]` | Collections (Python 3.9+) |
| `CourseId = int` | Type alias |
| `Annotated[int, Path(gt=0)]` | int + extra info FastAPI reads |

## Interview questions
1. **Does Python enforce type hints at runtime?** No. They're used by editors, type checkers (mypy) and libraries like FastAPI/Pydantic.
2. **`Optional[int]` vs a default value?** `Optional[int]` means the value may be `None`; a default value means the argument can be skipped. Often used together, but different.
3. **How does FastAPI use type hints?** To convert incoming data, validate it, return clear 422 errors, and generate API docs automatically.

## Homework
Open `homework.py`, add the correct type hints, and run `mypy --strict homework.py` until it says **Success**. Answer at the start of Video 5.

## Homework answer
```python
from typing import Any


def full_name(first: str, last: str, middle: str | None = None) -> str:
    if middle:
        return f"{first} {middle} {last}"
    return f"{first} {last}"


def average(marks: list[float]) -> float:
    return sum(marks) / len(marks)


def find_course(courses: list[dict[str, Any]], course_id: int) -> dict[str, Any] | None:
    for course in courses:
        if course["id"] == course_id:
            return course
    return None
```
`mypy --strict homework.py` → **Success: no issues found**
