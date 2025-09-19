from __future__ import annotations

import hashlib
import json
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models


def compute_state_hash(
    *,
    state_snapshot: dict,
    actions: Iterable[dict],
    previous_hash: str,
) -> str:
    payload = {
        "state": state_snapshot,
        "actions": list(actions),
        "prev": previous_hash,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


async def append_replay_log(
    session: AsyncSession,
    *,
    tick: int,
    state_snapshot: dict,
    actions: List[dict],
    previous_hash: str,
) -> models.ReplayLog:
    state_hash = compute_state_hash(
        state_snapshot=state_snapshot, actions=actions, previous_hash=previous_hash
    )
    replay = models.ReplayLog(
        tick=tick,
        state_hash=state_hash,
        prev_hash=previous_hash,
        actions={"actions": actions},
    )
    session.add(replay)
    await session.flush()
    return replay


async def verify_replay(
    session: AsyncSession,
    *,
    start: int,
    end: int,
) -> bool:
    stmt = (
        select(models.ReplayLog)
        .where(models.ReplayLog.tick.between(start, end))
        .order_by(models.ReplayLog.tick)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    prev_hash = "0" * 64
    for row in rows:
        expected = compute_state_hash(
            state_snapshot={"tick": row.tick},
            actions=row.actions.get("actions", []),
            previous_hash=prev_hash,
        )
        if expected != row.state_hash:
            return False
        prev_hash = row.state_hash
    return True
