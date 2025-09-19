from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class ValidationError(Exception):
    pass


class RulesetContext(Protocol):
    session: AsyncSession
    tick: int


Validator = Callable[[RulesetContext, Dict[str, Any]], Awaitable[None]]
Applier = Callable[[RulesetContext, Dict[str, Any]], Awaitable[Dict[str, Any]]]


@dataclass
class ActionDefinition:
    name: str
    validator: Validator
    applier: Applier


class Ruleset:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    async def setup(self, session: AsyncSession) -> None:  # pragma: no cover - hook
        return None
