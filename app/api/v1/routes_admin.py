from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.ticks import TickManager, verify_replay_range
from app.domain import models
from app.infra.db import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


def ensure_dev_mode() -> None:
    if not get_settings().dev_mode:
        raise HTTPException(status_code=403, detail="admin disabled")


@router.post("/tick/advance")
async def advance_tick(session: AsyncSession = Depends(get_session)) -> dict:
    ensure_dev_mode()
    manager = TickManager(session)
    result = await manager.advance_tick()
    return result


@router.post("/world/reset")
async def reset_world(session: AsyncSession = Depends(get_session)) -> dict:
    ensure_dev_mode()
    for model in [
        models.Event,
        models.Action,
        models.MarketListing,
        models.CurrencyPacket,
        models.Entity,
        models.ReplayLog,
    ]:
        await session.execute(delete(model))
    world = await session.get(models.World, 1)
    if world is None:
        world = models.World(id=1)
        session.add(world)
    else:
        world.tick = 0
    await session.flush()
    return {"tick": world.tick}


@router.get("/replay/verify")
async def replay_verify(
    from_tick: int = Query(0, alias="from"),
    to_tick: int = Query(0, alias="to"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    ensure_dev_mode()
    valid = await verify_replay_range(session, start=from_tick, end=to_tick)
    return {"valid": valid}
