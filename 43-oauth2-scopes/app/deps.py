# The current user - and the SCOPES this endpoint needs
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.roles import ROLE_SCOPES, SCOPES, Role
from app.security import decode_access_token

DB = Annotated[AsyncSession, Depends(get_db)]

# scopes=...: OpenAPI lists them, and Swagger's Authorize dialog shows a checkbox for each
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scopes=SCOPES)


async def get_current_user(security_scopes: SecurityScopes,
                           token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    # security_scopes.scopes: every scope that THIS request needs, from all Security(...)
    header = "Bearer"
    if security_scopes.scopes:
        header = f'Bearer scope="{security_scopes.scope_str}"'   # what is needed
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail="Could not validate credentials",
                                      headers={"WWW-Authenticate": header})
    try:
        claims = decode_access_token(token)
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise credentials_error from None
    token_scopes = claims.get("scope", "").split()
    user = await db.get(User, user_id)
    if user is None:
        raise credentials_error
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    for scope in security_scopes.scopes:
        if scope not in token_scopes:                       # the TOKEN may not do it
            raise scope_error(scope, security_scopes, "The token doesn't have the scope")
        if scope not in ROLE_SCOPES[Role(user.role)]:      # the USER may not (any more)
            raise scope_error(scope, security_scopes, "Your role doesn't allow the scope")
    return user


def scope_error(scope: str, security_scopes: SecurityScopes, why: str) -> HTTPException:
    # RFC 6750: insufficient_scope -> 403, and the header says which scopes are needed
    header = f'Bearer error="insufficient_scope", scope="{security_scopes.scope_str}"'
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"{why}: {scope}",
                         headers={"WWW-Authenticate": header})


Me = Annotated[User, Security(get_current_user, scopes=["me"])]
CourseReader = Annotated[User, Security(get_current_user, scopes=["courses:read"])]
CourseWriter = Annotated[User, Security(get_current_user, scopes=["courses:write"])]
