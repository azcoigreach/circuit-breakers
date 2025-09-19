from __future__ import annotations

from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import events, replay
from app.domain import models
from app.domain.rules.base_ruleset import ValidationError
from app.domain.services.action_service import ActionService
from app.domain.services.market_service import MarketService


class TickManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.action_service = ActionService(session)
        self.market_service = MarketService(session)

    async def ensure_world(self) -> models.World:
        world = await self.session.get(models.World, 1)
        if world is None:
            world = models.World(id=1)
            self.session.add(world)
            await self.session.flush()
        return world

    async def get_world_state(self) -> models.World:
        return await self.ensure_world()

    async def enqueue_actions(self, *, actions: List[Dict[str, object]]) -> List[models.Action]:
        world = await self.ensure_world()
        return await self.action_service.enqueue_actions(tick=world.tick, actions=actions)

    async def advance_tick(self) -> Dict[str, object]:
        world = await self.ensure_world()
        current_tick = world.tick
        applied_actions = await self.action_service.apply_actions(tick=current_tick)
        world.tick += 1
        await self.session.flush()

        await events.record_event(
            self.session,
            tick=world.tick,
            kind="tick.advance",
            subject_id=None,
            payload={"tick": world.tick},
        )

        state_snapshot = await self._snapshot_state(world.tick)
        previous_hash = await self._previous_hash(world.tick)
        await replay.append_replay_log(
            self.session,
            tick=world.tick,
            state_snapshot=state_snapshot,
            actions=applied_actions,
            previous_hash=previous_hash,
        )
        return {"tick": world.tick, "applied": applied_actions}

    async def _snapshot_state(self, tick: int) -> Dict[str, object]:
        players_stmt = select(models.Player.id, models.Player.balance_mamp).order_by(
            models.Player.id
        )
        players_result = await self.session.execute(players_stmt)
        players = [
            {"id": str(row.id), "balance_mamp": int(row.balance_mamp)}
            for row in players_result
        ]
        listings_stmt = select(models.MarketListing.id, models.MarketListing.status).order_by(
            models.MarketListing.id
        )
        listings_result = await self.session.execute(listings_stmt)
        listings = [
            {"id": str(row.id), "status": row.status.value}
            for row in listings_result
        ]
        return {
            "tick": tick,
            "players": players,
            "listings": listings,
        }

    async def _previous_hash(self, tick: int) -> str:
        if tick <= 1:
            return "0" * 64
        stmt = select(models.ReplayLog.state_hash).where(models.ReplayLog.tick == tick - 1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() or ("0" * 64)


async def verify_replay_range(session: AsyncSession, *, start: int, end: int) -> bool:
    return await replay.verify_replay(session, start=start, end=end)


async def enqueue_with_validation(
    manager: TickManager,
    *,
    actions: List[Dict[str, object]],
) -> List[models.Action]:
    try:
        return await manager.enqueue_actions(actions=actions)
    except ValidationError as exc:  # pragma: no cover - defensive
        raise ValueError(str(exc)) from exc
