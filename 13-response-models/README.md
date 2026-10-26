# Video 13 – Response Models and Status Codes

📺 Playlist: https://www.youtube.com/playlist?list=PLBjgbZvHwQmg

## Files
| File | What it shows |
|------|---------------|
| `main.py` | In/Out/DB models (`UserCreate`, `UserOut`, `UserInDB`), `response_model=`, return type as response model, `status_code=` (201, 204), `status.HTTP_...` constants, `response_model_exclude_none`, `responses={404: ...}`, choosing the status code at runtime with `Response` |
| `test_main.py` | 8 tests (passwords never returned, 201/200/204/404, OpenAPI shows the codes) |
| `homework_video12.py` | Answer to the Video 12 homework (`OrderCreate`) |

## Run it
```bash
pip install -r requirements.txt
fastapi dev main.py
pytest -v
```

## Three models for one resource
| Model | Used for | Has |
|-------|----------|-----|
| `UserCreate` | request body (IN) | name, email, **password**, bio |
| `UserOut` | response (OUT) | id, name, email, bio – **no password** |
| `UserInDB(UserOut)` | what we store | everything in `UserOut` + **hashed_password** |

## Status codes used
| Endpoint | Code |
|----------|------|
| `POST /users` | **201 Created** |
| `GET /users`, `GET /users/{id}` | **200 OK** / **404 Not Found** |
| `DELETE /users/{id}` | **204 No Content** (no body) |
| `PUT /users/{id}` | **201** if it created a new user, **200** if it replaced one |
| invalid body | **422** (automatic) |
| response doesn't match the response model | **500** – `ResponseValidationError` (a bug in *your* code) |

## Interview questions
1. **What is `response_model` and why use it?** It declares the shape of the response. FastAPI validates and *filters* the returned data to that model, so extra fields (like a password hash) are never sent, and the response schema appears in the OpenAPI docs. A return type annotation does the same.
2. **Why separate input and output models?** The client sends different data than it should receive: a password goes in but must never come out; ids and timestamps come out but aren't sent in. Separate models make leaks impossible and the docs accurate.
3. **How do you set status codes in FastAPI?** With `status_code=` in the decorator (e.g. `status.HTTP_201_CREATED`, `204` for delete), with `HTTPException(status_code=...)` for errors, or at runtime through a `Response` parameter (`response.status_code = ...`).

## Homework
1. Create `CourseIn` (title, price, `internal_notes`) and `CourseOut` (id, title, price) – `internal_notes` must never be returned.
2. `POST /courses` → 201 with `CourseOut`; `GET /courses` → `list[CourseOut]`.
3. `DELETE /courses/{course_id}` → 204, or 404 if not found.
4. Add `responses={404: {"description": "Course not found"}}` to the delete route.
Answer at the start of Video 14.
