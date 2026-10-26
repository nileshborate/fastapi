# Video 13 - Response Models and Status Codes
# Run:  fastapi dev main.py     ->  http://127.0.0.1:8000/docs
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Path, Response, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Course Hub API", version="1.6.0")


# 1. IN model: what the client SENDS
class UserCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)
    bio: str | None = None


# 2. OUT model: what we SEND BACK (no password!)
class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    bio: str | None = None


# 3. Stored model: everything we keep (adds the hashed password)
class UserInDB(UserOut):
    hashed_password: str


USERS: dict[int, UserInDB] = {}


def fake_hash(password: str) -> str:
    # NOT real security - real password hashing comes in the security videos
    return "hashed-" + password[::-1]


def to_db(user_id: int, user: UserCreate) -> UserInDB:
    return UserInDB(id=user_id, name=user.name, email=user.email, bio=user.bio, hashed_password=fake_hash(user.password))


# response_model filters the output: hashed_password is never sent
@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate) -> Any:
    user_id = max(USERS, default=0) + 1
    USERS[user_id] = to_db(user_id, user)
    return USERS[user_id]


# The return type annotation works as the response model too
@app.get("/users")
def list_users() -> list[UserOut]:
    return list(USERS.values())


@app.get(
    "/users/{user_id}",
    response_model_exclude_none=True,
    responses={404: {"description": "User not found"}},
)
def get_user(user_id: Annotated[int, Path(gt=0)]) -> UserOut:
    if user_id not in USERS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return USERS[user_id]


# 204 No Content: success, but no body
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: Annotated[int, Path(gt=0)]) -> None:
    if USERS.pop(user_id, None) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


# Choose the status code at runtime with the Response parameter
@app.put("/users/{user_id}")
def put_user(user_id: Annotated[int, Path(gt=0)], user: UserCreate, response: Response) -> UserOut:
    if user_id not in USERS:
        response.status_code = status.HTTP_201_CREATED      # created a new one
    USERS[user_id] = to_db(user_id, user)
    return USERS[user_id]
