from __future__ import annotations

import asyncio
import json
from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.infra.db import get_session
from app.infra.redis import pubsub
from app.domain import models

router = APIRouter(tags=["stream"], prefix="")


@router.get("/events", response_model=List[schemas.EventSchema])
async def list_events(
    since_tick: int = 0,
    session: AsyncSession = Depends(get_session),
) -> List[schemas.EventSchema]:
    stmt = (
        select(models.Event)
        .where(models.Event.tick >= since_tick)
        .order_by(models.Event.tick, models.Event.created_at)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()
    return [
        schemas.EventSchema(
            id=event.id,
            tick=event.tick,
            kind=event.kind,
            subject_id=event.subject_id,
            payload=event.payload,
        )
        for event in events
    ]


@router.websocket("/ws")
async def websocket_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    queue: asyncio.Queue[dict] = asyncio.Queue()

    def callback(message: dict) -> None:
        queue.put_nowait(message)

    pubsub.subscribe("events", callback)
    try:
        while True:
            message = await queue.get()
            await websocket.send_text(json.dumps({"events": [message]}))
    except WebSocketDisconnect:
        return
