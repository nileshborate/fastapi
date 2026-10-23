# Video 11 – Pydantic Field(): Rules, Email, Defaults and Examples

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | `StudentCreate` with `Field()` rules: `min_length`/`max_length`, `ge`/`le`, `strict`, `pattern`, `EmailStr`, `default_factory`, `examples`, `description`; the `Annotated` style |
| `test_main.py` | 10 tests – one for every rule |
| `homework_video10.py` | Answer to the Video 10 homework (`StudentCreate`, `POST /students`, `PUT /students/{student_id}`) |

## Run it
```bash
pip install -r requirements.txt     # fastapi[standard] already includes email-validator
fastapi dev main.py                 # open /docs -> POST /students -> see the example body
pytest -v
```

## Field() cheat sheet
| Rule | Works on | Example | Error type |
|------|----------|---------|------------|
| `min_length`, `max_length` | str, list | `Field(min_length=2, max_length=50)` | `string_too_short`, `too_long` |
| `ge`, `le`, `gt`, `lt` | numbers | `Field(ge=10, le=100)` | `greater_than_equal`, `less_than_equal` |
| `pattern` | str | `Field(pattern=r"^[6-9]\d{9}$")` | `string_pattern_mismatch` |
| `strict=True` | any | `"20"` is **not** converted to `20` | `int_type` |
| `EmailStr` (type) | str | `email: EmailStr` | `value_error` |
| `default` / `default_factory` | any | `Field(default_factory=list)` | – |
| `examples`, `description` | any | shown in `/docs` | – |

## Try these bodies on `POST /students`
| Body | Result |
|------|--------|
| `{"name": "Asha Patil", "email": "asha@example.com"}` | 201 – `age`, `phone` = null, `courses` = [] |
| `{"name": "A", ...}` | 422 – `String should have at least 2 characters` |
| `{"email": "not-an-email", ...}` | 422 – `value is not a valid email address` |
| `{"age": 5, ...}` | 422 – `Input should be greater than or equal to 10` |
| `{"age": "20", ...}` | 422 – strict: `Input should be a valid integer` |
| `{"phone": "12345", ...}` | 422 – `String should match pattern '^[6-9]\d{9}$'` |
| `{"courses": [1, 2, 3, 4, 5, 6], ...}` | 422 – `List should have at most 5 items` |

## Interview questions
1. **What is Pydantic's `Field()` used for?** To add validation rules (length, number limits, regex pattern, strict mode) and metadata (default, default_factory, description, examples) to a single model field. The rules also appear in the OpenAPI schema and Swagger.
2. **`Field()` vs `Query()` / `Path()`?** Same idea and the same rules (`ge`, `le`, `min_length`, `pattern`…). `Field()` is for fields inside a Pydantic model (usually the body); `Query()` and `Path()` are for function parameters that come from the URL.
3. **Why use `default_factory`?** It calls a function to create a new default value for every object – needed for dynamic values like the current time or a new UUID, and the clear way to give each object its own list or dict.

## Homework
Make a `CourseCreate` model with `Field()`:
1. `title`: 3–100 characters, with an example.
2. `price`: 0 to 50000, default 0, with a description.
3. `level`: only `beginner`, `intermediate` or `advanced` – use a `pattern`.
4. `tags`: a list of strings, default empty (`default_factory`), max 5 tags.
Answer at the start of Video 12.

## Homework answer (shown at the start of Video 12)
```python
class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100, examples=["FastAPI Basics"])
    price: int = Field(default=0, ge=0, le=50000, description="Price in rupees")
    level: str = Field(default="beginner", pattern=r"^(beginner|intermediate|advanced)$")
    tags: list[str] = Field(default_factory=list, max_length=5)
```
Full file: [`../12-pydantic-validators/homework_video11.py`](../12-pydantic-validators/homework_video11.py)
