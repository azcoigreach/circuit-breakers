from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.core.auth import authenticate_token
from app.core.ticks import TickManager
from app.domain.rules.base_ruleset import ValidationError
from app.infra.db import get_session

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/", response_model=schemas.EnqueueResponse)
async def submit_actions(
    submission: schemas.ActionSubmission,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.EnqueueResponse:
    manager = TickManager(session)
    actions_payload: List[dict] = []
    for action in submission.actions:
        if action.actor_id != player.id:
            raise HTTPException(status_code=403, detail="Actor mismatch")
        actions_payload.append(action.model_dump())
    try:
        accepted = await manager.enqueue_actions(actions=actions_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    world = await manager.get_world_state()
    return schemas.EnqueueResponse(
        accepted=[action.id for action in accepted],
        tick=world.tick,
    )
