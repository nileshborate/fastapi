# Video 10 – Request Body with Pydantic

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | `BaseModel` (`CourseCreate`, `Review`), `POST /courses` (201), `PUT /courses/{course_id}`, path + body + query together |
| `test_main.py` | 8 tests (a fixture resets the data before each test) |
| `homework_video9.py` | Answer to the Video 9 homework (`max_price`, `sort_by`, `level` on `/search`) |

## Run it
```bash
pip install -r requirements.txt
fastapi dev main.py        # open http://127.0.0.1:8000/docs  (browsers can't send POST from the address bar)
pytest -v
```

## Try it with curl
```bash
curl -X POST http://127.0.0.1:8000/courses \
     -H "Content-Type: application/json" \
     -d '{"title": "Testing FastAPI", "price": 299}'

curl -X PUT http://127.0.0.1:8000/courses/2 \
     -H "Content-Type: application/json" \
     -d '{"title": "Pydantic V2", "price": 599}'

curl -X POST "http://127.0.0.1:8000/courses/1/reviews?notify=true" \
     -H "Content-Type: application/json" \
     -d '{"student": "Asha", "rating": 5}'
```

## What happens with different bodies
| Body | Result |
|------|--------|
| `{"title": "Testing FastAPI", "price": 299}` | 201 – defaults fill `level`, `published`, `description` |
| `{"price": 299}` | 422 – `Field required`, `loc: ["body", "title"]` |
| `{"title": "X", "price": "abc"}` | 422 – `Input should be a valid integer` |
| `{"title": "X", "price": "499"}` | 201 – `"499"` is converted to `499` |
| `{"title": "X", "teacher": "Nilesh"}` | 201 – unknown fields are ignored |
| `{"title": "X",}` (broken JSON) | 422 – `JSON decode error` |

## Key ideas
- A **Pydantic model** (`class CourseCreate(BaseModel)`) describes the JSON body. Field without default = required; with default = optional.
- A function argument whose type is a Pydantic model is read from the **request body**.
- Use attributes (`course.title`), not `course["title"]`. `course.model_dump()` → a normal `dict`.
- **POST** creates (201 Created). **PUT** replaces the whole resource (fields you don't send go back to their defaults).
- FastAPI's rule: name in the path → **path**; simple type → **query**; Pydantic model → **body**.

## Interview questions
1. **Why use Pydantic models for the request body?** One class gives you parsing of the JSON, validation with clear 422 errors, type conversion, defaults, editor autocompletion, and automatic documentation in OpenAPI / Swagger.
2. **POST vs PUT?** POST creates a new resource (the server chooses the id, returns 201). PUT replaces an existing resource at a known URL with the full new representation; repeating the same PUT gives the same result (idempotent).
3. **How does FastAPI know a parameter comes from the body?** Its type is a Pydantic model (or it's declared with `Body()`). Path names come from the path, simple types become query parameters.

## Homework
1. Create a `StudentCreate` model: `name` (str), `email` (str), `age` (int, optional), `courses` (list[int], default empty list).
2. Add `POST /students` (201) that stores students in a `STUDENTS` list with an auto id.
3. Add `PUT /students/{student_id}` with 404 when not found.
Answer at the start of Video 11.

## Homework answer (shown at the start of Video 11)
```python
class StudentCreate(BaseModel):
    name: str
    email: str
    age: int | None = None
    courses: list[int] = []      # Pydantic copies this default, so it's safe


@app.post("/students", status_code=201)
def create_student(student: StudentCreate) -> dict[str, Any]:
    new_student = {"id": next_id(), **student.model_dump()}
    STUDENTS.append(new_student)
    return new_student


@app.put("/students/{student_id}")
def replace_student(student_id: Annotated[int, Path(gt=0)], student: StudentCreate) -> dict[str, Any]:
    for index, existing in enumerate(STUDENTS):
        if existing["id"] == student_id:
            updated = {"id": student_id, **student.model_dump()}
            STUDENTS[index] = updated
            return updated
    raise HTTPException(status_code=404, detail="Student not found")
```
Full file: [`../11-pydantic-field/homework_video10.py`](../11-pydantic-field/homework_video10.py)
