# Video 12 – Pydantic Part 2: Validators, Nested Models and model_config

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | `@field_validator` (check, clean, `mode="before"`), `@model_validator(mode="after")`, nested models (`Instructor`), lists of models (`list[Lesson]`), `model_config = ConfigDict(...)` |
| `test_main.py` | 10 tests, including the error *locations* for nested data |
| `homework_video11.py` | Answer to the Video 11 homework (`CourseCreate` with `Field()`) |

## Run it
```bash
pip install -r requirements.txt
fastapi dev main.py
pytest -v
```

## Example body for POST /courses
```json
{
  "title": "FastAPI Basics",
  "price": 999,
  "start_date": "2026-11-01",
  "end_date": "2026-11-30",
  "tags": "Python, FastAPI",
  "instructor": {"name": "Nilesh Borate", "email": "nilesh@example.com"},
  "lessons": [
    {"title": "Intro", "minutes": 15},
    {"title": "Routes", "minutes": 25}
  ]
}
```

## What happens
| Change | Result |
|--------|--------|
| `"title": "FASTAPI BASICS"` | 422 – `Value error, title must not be ALL CAPS` (field_validator) |
| `"tags": [" FastAPI", "python", "fastapi "]` | cleaned to `["fastapi", "python"]` |
| `"tags": "Python, FastAPI"` | `mode="before"` splits the text → `["fastapi", "python"]` |
| `"end_date": "2026-10-01"` | 422 – `loc: ["body"]` (model_validator) |
| `"discount_price": 999` | 422 – `discount_price must be lower than price` |
| `"instructor": {"email": "wrong", ...}` | 422 – `loc: ["body", "instructor", "email"]` |
| a lesson with `"minutes": 0` | 422 – `loc: ["body", "lessons", 1, "minutes"]` |
| `"title": "   FastAPI Basics   "` | stripped (`str_strip_whitespace=True`) |
| `"teacher": "Nilesh"` | 422 – `extra_forbidden` (`extra="forbid"`) |
| `"start_date": "01-11-2026"` | 422 – dates must be ISO: `YYYY-MM-DD` |

## Order of validation
1. `mode="before"` field validators (raw input)
2. Type conversion + `Field()` rules
3. `mode="after"` field validators (default)
4. `@model_validator(mode="after")` – the whole object, all fields ready

## Interview questions
1. **`field_validator` vs `model_validator`?** A field validator checks or cleans one field and receives only that value. A model validator (`mode="after"`) receives the whole validated object, so it can compare fields – e.g. end date after start date. Raising `ValueError` in either gives a 422.
2. **How are nested models validated, and how do you find the error?** Each nested model is validated with its own rules, recursively, including every item of a `list[Model]`. The error's `loc` gives the full path, e.g. `["body", "lessons", 1, "minutes"]`.
3. **What is `model_config`?** Settings for the whole model via `ConfigDict`, e.g. `str_strip_whitespace=True`, `extra="forbid"` (reject unknown fields), `frozen=True` (immutable), `from_attributes=True` (read from ORM objects – used later with databases).

## Homework
Create an `OrderCreate` model:
1. `items`: a list of `OrderItem` (nested: `course_id` > 0, `quantity` 1–10), at least 1 item.
2. `coupon`: optional; a `field_validator` turns it into UPPER CASE and allows only letters and digits.
3. A `model_validator`: if `coupon` is `"FREE100"`, the order can have only 1 item.
4. `model_config` with `extra="forbid"`.
Answer at the start of Video 13.
