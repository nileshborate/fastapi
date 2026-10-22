# Video 6 - your first app in the new environment
# Run:  fastapi dev main.py     then open  http://127.0.0.1:8000  and  /docs

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "My FastAPI environment works!"}
