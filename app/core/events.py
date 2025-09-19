from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models
from app.infra.redis import pubsub


async def record_event(
    session: AsyncSession,
    *,
    tick: int,
    kind: str,
    subject_id: uuid.UUID | None,
    payload: Dict[str, Any],
) -> models.Event:
    event = models.Event(
        tick=tick,
        kind=kind,
        subject_id=subject_id,
        payload=payload,
    )
    session.add(event)
    await session.flush()
    pubsub.publish(
        "events",
        {
            "id": str(event.id),
            "tick": event.tick,
            "kind": event.kind,
            "subject_id": str(event.subject_id) if event.subject_id else None,
            "payload": event.payload,
        },
    )
    return event


async def bulk_events(
    session: AsyncSession,
    *,
    tick: int,
    events: Iterable[tuple[str, uuid.UUID | None, Dict[str, Any]]],
) -> List[models.Event]:
    stored: List[models.Event] = []
    for kind, subject_id, payload in events:
        stored.append(
            await record_event(
                session, tick=tick, kind=kind, subject_id=subject_id, payload=payload
            )
        )
    return stored
