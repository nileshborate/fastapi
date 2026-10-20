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
