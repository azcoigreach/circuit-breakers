from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class InMemoryPubSub:
    subscribers: Dict[str, List[Callable[[Any], None]]] = field(default_factory=dict)

    def publish(self, channel: str, message: Any) -> None:
        for callback in self.subscribers.get(channel, []):
            callback(message)

    def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        self.subscribers.setdefault(channel, []).append(callback)


pubsub = InMemoryPubSub()
