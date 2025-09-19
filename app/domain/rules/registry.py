from __future__ import annotations

from typing import Dict

from app.domain.rules.base_ruleset import ActionDefinition


class RulesetRegistry:
    def __init__(self) -> None:
        self._actions: Dict[str, ActionDefinition] = {}

    def register_action(self, definition: ActionDefinition) -> None:
        self._actions[definition.name] = definition

    def get(self, name: str) -> ActionDefinition:
        if name not in self._actions:
            raise KeyError(f"Unknown action: {name}")
        return self._actions[name]

    def actions(self) -> Dict[str, ActionDefinition]:
        return dict(self._actions)


registry = RulesetRegistry()
