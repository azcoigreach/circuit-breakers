from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.core.ticks import TickManager
from app.infra.db import get_session

router = APIRouter(prefix="/world", tags=["world"])


@router.get("/", response_model=schemas.WorldState)
async def get_world(session: AsyncSession = Depends(get_session)) -> schemas.WorldState:
    manager = TickManager(session)
    world = await manager.get_world_state()
    return schemas.WorldState(
        tick=world.tick,
        seed=world.seed,
        ruleset_version=world.ruleset_version,
    )
