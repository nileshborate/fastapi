# 14 – Error Handling the Right Way

**FastAPI Mastery: Zero to Production** – Video 14 · Nilesh Technology

Every error your API sends should look the **same**, use the **right status code**, and **never leak** internal details.

## Files
| File | What it shows |
|------|---------------|
| `main.py` | `HTTPException` (detail as text or dict, headers), custom exceptions, 4 exception handlers, a safe 500 |
| `test_main.py` | 8 tests (`pytest -v`) |
| `homework_video13.py` | Answer to the Video 13 homework (`CourseIn` / `CourseOut`) |

## Run it
```bash
cd 14-error-handling
pip install -r requirements.txt
fastapi dev main.py        # http://127.0.0.1:8000/docs
pytest -v                  # 8 passed
```

## One error format for the whole API
```json
{"error": {"code": "COURSE_FULL", "message": "Course 2 has no free seats", "path": "/courses/2/enroll"}}
```

| Situation | How | Status |
|-----------|-----|--------|
| Not found | `raise HTTPException(404, detail="Course not found", headers={...})` | 404 |
| Extra info in the error | `HTTPException(detail={"code": ..., "message": ..., ...})` | any |
| Business rule broken | `raise CourseFullError(course_id)` + `@app.exception_handler(CourseHubError)` | 409 |
| Invalid request | custom `RequestValidationError` handler | 422 |
| Unknown URL | `StarletteHTTPException` handler (FastAPI's own 404s too) | 404 |
| A bug in our code | `Exception` handler → log it, send a safe message | 500 |

## Key rules
- **`raise`** `HTTPException` – never `return` it (returning gives status **200**!).
- Register the handler for **Starlette's** `HTTPException` so that FastAPI's own errors (like "Not Found" for unknown URLs) use your format too.
- Never send a traceback or exception text to the client. **Log** it on the server.

## Interview questions
1. **What is the difference between `HTTPException` and a custom exception with a handler?** `HTTPException` is quick: you raise it with a status code and detail. A custom exception describes a *business* error (`CourseFullError`) and keeps HTTP out of your business code; one `@app.exception_handler` turns all of them into a consistent response.
2. **How do you change FastAPI's 422 validation response?** Add `@app.exception_handler(RequestValidationError)`, read `exc.errors()` (each has `loc`, `msg`, `type`) and return your own `JSONResponse` with status 422.
3. **How should an API handle unexpected errors (500)?** Catch them with an `Exception` handler, log the full traceback on the server, and return a generic message – never the exception text or stack trace, because that leaks internal details.

## Homework
1. Create `ProductNotFoundError(product_id)` and `OutOfStockError(product_id)` that inherit from a base `ShopError` with `code`, `message`, `status_code`.
2. Write one `@app.exception_handler(ShopError)` returning `{"error": {"code", "message"}}`.
3. `POST /products/{product_id}/buy` → 404 / 409 / 200 using those exceptions.
4. Bonus: add a `request_id` (e.g. `uuid4()`) to the 500 response and to the log line.

Answer at the start of Video 15.

## Homework answer
The answer is in [`../15-headers-cookies-forms-files/homework_video14.py`](../15-headers-cookies-forms-files/homework_video14.py): a `ShopError` base class with `ProductNotFoundError` (404) and `OutOfStockError` (409), one `@app.exception_handler(ShopError)`, `POST /products/{product_id}/buy`, and the bonus: a `request_id` (`uuid4().hex`) in the safe 500 response and in the log line.
