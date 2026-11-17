# Video 54 - API versioning: v1 and v2 side by side, each with its own docs
# fastapi dev app/main.py  ->  /v1/docs  ·  /v2/docs
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Response

from app import store
from app.deprecation import DeprecationMiddleware, v1_usage
from app.v1 import routes as v1_routes
from app.v1.schemas import CourseV1
from app.v2 import routes as v2_routes
from app.v2.schemas import CourseV2

v1 = FastAPI(title="Course Hub API", version="1.0.0", description="Deprecated - use v2")
v1.include_router(v1_routes.router, deprecated=True)     # crossed out in /v1/docs
v1.add_middleware(DeprecationMiddleware)

v2 = FastAPI(title="Course Hub API", version="2.0.0")
v2.include_router(v2_routes.router)

app = FastAPI(title="Course Hub", docs_url=None, redoc_url=None)
app.mount("/v1", v1)                        # a whole app under /v1 - its own /v1/docs
app.mount("/v2", v2)

V1_TYPE = "application/vnd.coursehub.v1+json"
V2_TYPE = "application/vnd.coursehub.v2+json"


@app.get("/courses/{course_id}", tags=["Header versioning"])
def read_course_by_header(course_id: int, response: Response,
                          accept: Annotated[str, Header()] = V1_TYPE,
                          api_version: Annotated[str | None, Header()] = None,
                          ) -> CourseV1 | CourseV2:
    """the other way: ONE url - the client picks the version in a header"""
    if api_version is None:                 # homework 54: API-Version wins over Accept
        api_version = "2" if V2_TYPE in accept else "1"
    if api_version not in ("1", "2"):
        raise HTTPException(status_code=400,
                            detail=f"Unknown API version: {api_version}. Use 1 or 2.")
    record = store.get_course(course_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Course not found")
    response.headers["Vary"] = "Accept, API-Version"     # caches: same url, different answers
    if api_version == "2":
        return CourseV2.from_record(record)
    return CourseV1.from_record(record)     # no version asked = what old clients got


@app.get("/admin/v1-usage", tags=["Admin"])
def v1_clients() -> dict[str, int]:
    return dict(v1_usage.most_common())     # who do we still have to call before the sunset?
