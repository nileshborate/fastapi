# Video 1 – What is FastAPI and Why Learn It?

A first look at FastAPI in 6 lines of code. (We set up Python and VS Code properly in Video 6 – this is just to see the magic.)

## Run it
```bash
pip install -r requirements.txt
fastapi dev main.py
```

## Try these in your browser
| URL | What you'll see |
|-----|-----------------|
| http://127.0.0.1:8000/courses/7 | `{"id": 7, "title": "FastAPI Mastery"}` |
| http://127.0.0.1:8000/courses/abc | 422 error: *Input should be a valid integer* – validation for free |
| http://127.0.0.1:8000/docs | Interactive docs – click **Try it out** → enter 7 → **Execute** |

## Homework
Write down 3 apps you use every day and guess 2 APIs each one calls. Post your answer in the YouTube comments!

## Homework – example answer
| App | APIs it might call |
|-----|--------------------|
| Swiggy / Zomato | Restaurant menu API, payment gateway API |
| Google Pay / PhonePe (UPI) | Bank balance API, UPI transfer API |
| Ola / Uber | Maps API, driver location API |

## Interview questions
1. **What is an API?** A contract that lets one program request data or actions from another in a fixed format, without knowing its internals.
2. **What is FastAPI built on?** Starlette (web layer) and Pydantic (data validation); it runs on an ASGI server like Uvicorn.
3. **WSGI vs ASGI?** WSGI handles one request per worker at a time (synchronous). ASGI is asynchronous, so one worker can serve many requests while others wait on I/O.
