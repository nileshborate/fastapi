# Run: python -m demos.chain   - in which ORDER does FastAPI run a dependency chain?
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

calls: list[str] = []


def get_db():  # noqa: ANN201
    calls.append("get_db: open")
    yield "db"
    calls.append("get_db: close (after the answer)")


def get_token() -> str:
    calls.append("get_token")
    return "eyJ..."


def get_current_user(token: Annotated[str, Depends(get_token)],
                     db: Annotated[str, Depends(get_db)]) -> str:
    calls.append("get_current_user")
    return "asha"


def get_current_active_user(user: Annotated[str, Depends(get_current_user)]) -> str:
    calls.append("get_current_active_user")
    return user


app = FastAPI()


@app.get("/courses")
def create(user: Annotated[str, Depends(get_current_active_user)],
           db: Annotated[str, Depends(get_db)]) -> dict:     # get_db a SECOND time
    calls.append("the endpoint")
    return {"user": user}


with TestClient(app) as client:
    client.get("/courses")
for number, name in enumerate(calls, 1):
    print(f"{number}. {name}")
