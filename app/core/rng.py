from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(slots=True)
class DeterministicRNG:
    seed: str

    def for_tick(self, tick: int, action_id: str) -> random.Random:
        composite_seed = f"{self.seed}:{tick}:{action_id}"
        return random.Random(composite_seed)
