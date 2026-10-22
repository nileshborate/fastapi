# Video 8 – Path Parameters

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | Typed path parameters, `Path(gt=0)` validation, 404 with `HTTPException`, route order, `Enum` parameters, multiple parameters, the `:path` converter |
| `test_main.py` | 8 tests: 200, 404, 422 (not an int, not > 0, bad enum), route order, multiple params, path converter |
| `homework_video7.py` | Answer to the Video 7 homework (`/contact`, async `/stats`) |

## Run it
```bash
pip install -r requirements.txt
fastapi dev main.py
pytest -v
```

## Try these URLs
| URL | Result |
|-----|--------|
| `/courses/2` | 200 – the course with id 2 |
| `/courses/99` | 404 – `{"detail": "Course not found"}` |
| `/courses/abc` | 422 – `Input should be a valid integer` |
| `/courses/0` | 422 – `Input should be greater than 0` |
| `/courses/latest` | 200 – works because it's declared **before** `/courses/{course_id}` |
| `/levels/beginner` | 200 – beginner courses |
| `/levels/expert` | 422 – `Input should be 'beginner', 'intermediate' or 'advanced'` |
| `/students/7/courses/2` | `{"student_id": 7, "course_id": 2}` |
| `/files/notes/week1/intro.txt` | `{"file_path": "notes/week1/intro.txt"}` |

## Key ideas
- `{course_id}` in the path + a function argument with the **same name** = a path parameter.
- The **type hint** (`int`) makes FastAPI convert `"2"` → `2` and reject `"abc"` with **422**.
- `Annotated[int, Path(gt=0)]` adds rules: `gt`, `ge`, `lt`, `le`.
- **422** = the request is invalid (validation). **404** = valid request, but the item doesn't exist.
- Routes are matched **top to bottom**: put `/courses/latest` **before** `/courses/{course_id}`.
- `class Level(str, Enum)` limits a parameter to fixed values and shows a dropdown in `/docs`.

## Interview questions
1. **What is a path parameter and how does FastAPI read it?** A variable part of the URL path, written as `{name}` in the route. FastAPI passes it to the function argument with the same name and converts/validates it using the type hint.
2. **422 vs 404 for `/courses/abc` and `/courses/99`?** `/courses/abc` → 422 Unprocessable Entity (validation failed: not an integer). `/courses/99` → 404 Not Found (valid integer, but no course with that id).
3. **Why does route order matter?** FastAPI matches routes top to bottom. If `/courses/{course_id}` comes first, `/courses/latest` is captured by it and fails validation (422). Declare fixed paths before parameterised ones.

## Homework
1. Add `GET /courses/{course_id}/title` → returns only the title (404 if not found).
2. Add `GET /levels/{level}/count` using the `Level` enum → returns `{"level": "...", "count": N}`.
3. Make `course_id` accept only values from 1 to 1000 using `Path()`.
Answer at the start of Video 9.
