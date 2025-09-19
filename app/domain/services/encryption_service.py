from __future__ import annotations

import hashlib
from typing import Dict, Optional


def verify_packet_solution(payload: Dict[str, object], solution: Dict[str, object]) -> Optional[int]:
    if payload.get("type") != "hash-chain":
        return None
    difficulty = int(payload.get("difficulty", 0))
    target = payload.get("target_prefix", "")
    if not isinstance(target, str):
        return None
    nonce = solution.get("nonce")
    if not isinstance(nonce, str):
        return None
    seed = str(payload.get("seed", ""))
    digest = hashlib.sha256(f"{seed}:{nonce}".encode("utf-8")).hexdigest()
    if not digest.startswith(target[:difficulty]):
        return None
    reward = payload.get("reward_mamp")
    if not isinstance(reward, int):
        return None
    return reward
