# 15 – Headers, Cookies, Forms and File Uploads

**FastAPI Mastery: Zero to Production** – Video 15 · Nilesh Technology

Path, query and JSON body are not the only ways a client sends data. This lesson covers the rest.

## Files
| File | What it shows |
|------|---------------|
| `main.py` | `Header()`, response headers, `Cookie()`, `set_cookie` / `delete_cookie`, `Form()`, a Pydantic form model, `File()` / `UploadFile`, type + size checks, multiple files |
| `test_main.py` | 12 tests (`pytest -v`) |
| `homework_video14.py` | Answer to the Video 14 homework (`ShopError` + handlers) |

## Run it
```bash
cd 15-headers-cookies-forms-files
pip install -r requirements.txt     # fastapi[standard] includes python-multipart (needed for forms and files)
fastapi dev main.py                 # http://127.0.0.1:8000/docs
pytest -v                           # 12 passed
```

## Where does the data come from?
| Data | Declare it with | Example |
|------|-----------------|---------|
| Header | `Annotated[str, Header()]` | `user_agent` reads `User-Agent` (`_` becomes `-`, case doesn't matter) |
| Cookie | `Annotated[str, Cookie()] = "light"` | the browser sends it back automatically |
| Form field | `Annotated[str, Form()]` | HTML forms, `application/x-www-form-urlencoded` |
| Form model | `Annotated[ContactForm, Form()]` | many form fields validated by one Pydantic model |
| Small file | `Annotated[bytes, File()]` | the whole file in memory |
| File | `UploadFile` | `filename`, `content_type`, `await file.read()` – stored on disk after 1 MB |
| Many files | `list[UploadFile]` | |

Set things on the response with a `Response` parameter:
`response.headers["Cache-Control"] = ...`, `response.set_cookie(...)`, `response.delete_cookie(...)`.

## Upload safety rules
1. Check `content_type` → **415** Unsupported Media Type.
2. Check the size → **413** Content Too Large.
3. **Never** save with the user's filename – create your own (`uuid4().hex`).

## Interview questions
1. **How does FastAPI map a `Header()` parameter to the HTTP header name?** It converts underscores to hyphens (`user_agent` → `User-Agent`), and header names are case-insensitive. Without `Header()`, the parameter would be a query parameter.
2. **`bytes` vs `UploadFile` – which one and why?** `bytes` reads the whole file into memory – fine for small files. `UploadFile` uses a spooled temporary file (memory first, then disk), gives `filename` and `content_type`, and has async methods (`read`, `seek`, `close`) – use it for real uploads.
3. **Can one endpoint receive a JSON body and form fields together?** No. A request has one body with one content type: JSON (`application/json`) *or* form data (`application/x-www-form-urlencoded` / `multipart/form-data`). Form data and files can be mixed, because both use `multipart/form-data`.

## Homework
1. `GET /courses/{course_id}` sets a cookie `last_viewed` (1 day).
2. `GET /recent` reads it: return the course, or "Nothing viewed yet" if there is no cookie.
3. `POST /courses/{course_id}/resources`: requires an `X-API-Key` header, a `title` form field, and a **PDF** file (`application/pdf`) up to **5 MB** → 201, 401, 413 or 415.

Answer at the start of Video 16.
