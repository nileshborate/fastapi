# Run: python -m demos.factory
# require_roles(...) is a FACTORY: every call builds a NEW dependency function
import asyncio

from fastapi import HTTPException

from app.deps import require_roles
from app.models import User
from app.roles import PERMISSIONS, Role


async def main() -> None:
    admins_only = require_roles(Role.ADMIN)
    staff = require_roles(Role.TEACHER, Role.ADMIN)
    print("admins_only:", admins_only.__qualname__, "  staff:", staff.__qualname__)
    print("the same function?", admins_only is staff)
    print("remembered roles:", admins_only.__closure__[0].cell_contents,
          staff.__closure__[0].cell_contents)

    ravi = User(id=2, email="ravi@example.com", full_name="Ravi", role="teacher",
                is_active=True)
    print("staff(ravi)      ->", (await staff(ravi)).email)
    try:
        await admins_only(ravi)
    except HTTPException as error:
        print("admins_only(ravi) ->", error.status_code, error.detail)

    print("\nthe permission map:")
    for role, permissions in PERMISSIONS.items():
        print(f"   {role:<8} {sorted(permissions)}")


if __name__ == "__main__":
    asyncio.run(main())
