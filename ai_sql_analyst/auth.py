from __future__ import annotations

from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from ai_sql_analyst.config import settings


@dataclass(frozen=True, slots=True)
class Principal:
    api_key: str
    workspace_id: str = "demo"


def require_api_key(x_api_key: str = Header(default="")) -> Principal:
    allowed_keys = settings.allowed_api_keys()
    if not allowed_keys:
        return Principal(api_key="", workspace_id="demo")
    if x_api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header.",
        )
    return Principal(api_key=x_api_key, workspace_id="demo")
