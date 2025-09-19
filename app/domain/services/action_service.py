from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Dict, Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models
from app.domain.rules import registry
from app.domain.rules.base_ruleset import ValidationError

PER_TICK_ACTION_LIMIT = 3


class ActionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def enqueue_actions(
        self,
        *,
        tick: int,
        actions: Iterable[Dict[str, object]],
    ) -> List[models.Action]:
        accepted: List[models.Action] = []
        counts: Dict[uuid.UUID, int] = defaultdict(int)
        for action_payload in actions:
            actor_id = uuid.UUID(str(action_payload["actor_id"]))
            counts[actor_id] += 1
            if counts[actor_id] > PER_TICK_ACTION_LIMIT:
                raise ValidationError("Action quota exceeded")
            action = models.Action(
                tick=tick,
                actor_id=actor_id,
                type=str(action_payload["type"]),
                payload=dict(action_payload.get("payload", {})),
            )
            self.session.add(action)
            accepted.append(action)
        await self.session.flush()
        return accepted

    async def actions_for_tick(self, tick: int) -> List[models.Action]:
        stmt = (
            select(models.Action)
            .where(models.Action.tick == tick)
            .order_by(models.Action.received_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def apply_actions(self, *, tick: int) -> List[Dict[str, object]]:
        actions = await self.actions_for_tick(tick)
        applied: List[Dict[str, object]] = []
        for action in actions:
            definition = registry.registry.get(action.type)
            if definition is None:
                raise ValidationError(f"Unknown action type: {action.type}")
            context = SimpleNamespace(session=self.session, tick=tick, action=action)
            await definition.validator(context, action.payload)
            result = await definition.applier(context, action.payload)
            applied.append(
                {
                    "id": str(action.id),
                    "type": action.type,
                    "payload": action.payload,
                    "result": result,
                }
            )
        return applied


class SimpleNamespace:
    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
