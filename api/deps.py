"""FastAPI dependencies (auth, etc.)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.auth import decode_access_token

http_bearer = HTTPBearer(
    description="JWT from `POST /admin/login` (Authorization: Bearer &lt;token&gt;)",
)


def get_current_admin_email(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
) -> str:
    email = decode_access_token(credentials.credentials)
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return email
