# Video 9 – Query Parameters

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | Pagination (`skip`, `limit`), optional filters (`level`, `published`), a required `q`, `Query()` rules, multiple values (`ids`), path + query together |
| `test_main.py` | 10 tests |
| `homework_video8.py` | Answer to the Video 8 homework |

## Run it
```bash
pip install -r requirements.txt
fastapi dev main.py
pytest -v
```

## Try these URLs
| URL | Result |
|-----|--------|
| `/courses` | all 5 courses (default `skip=0`, `limit=10`) |
| `/courses?limit=2` | first 2 courses |
| `/courses?skip=2&limit=2` | courses 3 and 4 (page 2) |
| `/courses?level=beginner` | beginner courses |
| `/courses?published=false` | unpublished courses (`false`, `0`, `no`, `off` all work) |
| `/courses?level=beginner&published=true` | filters combined |
| `/courses?limit=500` | 422 – `Input should be less than or equal to 100` |
| `/search` | 422 – `Field required` (q is required) |
| `/search?q=a` | 422 – `String should have at least 2 characters` |
| `/search?q=fastapi` | FastAPI Basics, Deploying FastAPI |
| `/courses/by-ids?ids=1&ids=3` | courses 1 and 3 |
| `/courses/2?include_price=true` | course 2 with its price |

## Key ideas
- Query string = everything after `?` → `key=value` pairs joined with `&`.
- Any function argument that is **not** in the path (and is a simple type) is a **query parameter**.
- **Default value → optional.** No default → **required** (even `str | None` without `= None` is required!).
- `bool` accepts `true/false`, `1/0`, `yes/no`, `on/off`.
- `Annotated[int, Query(ge=1, le=100)]`, `Annotated[str, Query(min_length=2, max_length=50)]`.
- A `list[...]` query parameter **needs `Query()`**, otherwise FastAPI expects it in the request body.
- Pagination: `skip = (page - 1) * limit`.

## Interview questions
1. **Path parameter vs query parameter?** A path parameter identifies a resource (`/courses/2`) and is required. A query parameter is optional extra information – filtering, searching, sorting, pagination (`/courses?level=beginner&limit=10`).
2. **How does FastAPI decide if an argument is a path or query parameter?** If its name appears in the path in `{ }`, it's a path parameter. Otherwise, a simple type (int, str, bool, Enum…) is a query parameter. Pydantic models are read from the body.
3. **How do you make a query parameter optional or required?** Give it a default (`= 10` or `= None`) → optional. No default → required; FastAPI returns 422 "Field required" if it's missing.

## Homework
1. Add a `max_price: int | None = None` filter to `/courses` (only courses with `price <= max_price`).
2. Add `sort_by` with an Enum of `title` or `price` to `/courses`.
3. Make `/search` also accept `level` as an optional filter.
Answer at the start of Video 10.

## Homework answer (shown at the start of Video 10)
```python
class SortBy(Enum):
    title = "title"
    price = "price"


@app.get("/courses")
def list_courses(
    ...,
    max_price: int | None = None,      # 1
    sort_by: SortBy | None = None,     # 2
) -> list[dict[str, Any]]:
    ...
    if max_price is not None:
        result = [course for course in result if course["price"] <= max_price]
    if sort_by is not None:
        result = sorted(result, key=lambda course: course[sort_by.value])
    return result[skip : skip + limit]


@app.get("/search")
def search_courses(q: ..., level: Level | None = None) -> list[dict[str, Any]]:   # 3
    ...
```
Full file: [`../10-request-body/homework_video9.py`](../10-request-body/homework_video9.py)
