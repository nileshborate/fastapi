# Router-level dependencies: they run for EVERY endpoint in this router
from fastapi import APIRouter, Depends

from app.dependencies import CurrentRole, DBSession, require_admin, verify_api_key

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_api_key), Depends(require_admin)],
)


@router.get("/stats")
def stats(db: DBSession, role: CurrentRole) -> dict[str, int | str]:
    return {"courses": db.count("courses"), "students": db.count("students"), "checked_by": role}
