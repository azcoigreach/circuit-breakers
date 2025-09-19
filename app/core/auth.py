from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models
from app.infra.db import get_session

security = HTTPBearer(auto_error=False)


async def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def authenticate_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> models.Player:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    token_hash = await hash_token(credentials.credentials)
    stmt = select(models.Player).where(models.Player.token_hash == token_hash)
    result = await session.execute(stmt)
    player: Optional[models.Player] = result.scalars().first()
    if player is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return player
