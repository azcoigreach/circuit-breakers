from __future__ import annotations

import uuid
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models
from app.domain.models import Denomination
from app.domain.services.encryption_service import verify_packet_solution

DENOMINATION_MULTIPLIER = {
    Denomination.mAMP: 1,
    Denomination.kAMP: 1_000,
    Denomination.MAMP: 1_000_000,
    Denomination.GAMP: 1_000_000_000,
}


class CurrencyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_balance(self, player_id: uuid.UUID) -> int:
        stmt = select(models.Player.balance_mamp).where(models.Player.id == player_id)
        result = await self.session.execute(stmt)
        balance = result.scalar_one()
        return int(balance)

    async def transfer(self, sender_id: uuid.UUID, recipient_id: uuid.UUID, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        sender = await self.session.get(models.Player, sender_id, with_for_update=True)
        recipient = await self.session.get(
            models.Player, recipient_id, with_for_update=True
        )
        if sender is None or recipient is None:
            raise ValueError("Invalid player")
        if sender.balance_mamp < amount:
            raise ValueError("Insufficient balance")
        sender.balance_mamp -= amount
        recipient.balance_mamp += amount
        await self.session.flush()

    async def adjust_balance(self, player_id: uuid.UUID, delta: int) -> int:
        player = await self.session.get(models.Player, player_id, with_for_update=True)
        if player is None:
            raise ValueError("Player not found")
        new_balance = player.balance_mamp + delta
        if new_balance < 0:
            raise ValueError("Insufficient balance")
        player.balance_mamp = new_balance
        await self.session.flush()
        return new_balance

    async def mint_encrypted_packet(
        self,
        owner_id: uuid.UUID,
        denom: Denomination,
        payload: Dict[str, object],
        created_tick: int,
    ) -> models.CurrencyPacket:
        packet = models.CurrencyPacket(
            owner_id=owner_id,
            denom=denom,
            payload=payload,
            encrypted=True,
            created_tick=created_tick,
        )
        self.session.add(packet)
        await self.session.flush()
        return packet

    async def list_packets(self, owner_id: uuid.UUID) -> List[models.CurrencyPacket]:
        stmt = select(models.CurrencyPacket).where(models.CurrencyPacket.owner_id == owner_id)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def decrypt_packet(
        self, owner_id: uuid.UUID, packet_id: uuid.UUID, solution: Dict[str, object]
    ) -> int:
        packet = await self.session.get(models.CurrencyPacket, packet_id, with_for_update=True)
        if packet is None or packet.owner_id != owner_id:
            raise ValueError("Packet not found")
        if not packet.encrypted:
            return DENOMINATION_MULTIPLIER[packet.denom]
        reward = verify_packet_solution(packet.payload, solution)
        if reward is None:
            raise ValueError("Invalid solution")
        packet.encrypted = False
        packet.payload["solution"] = solution
        amount = int(reward)
        player = await self.session.get(models.Player, owner_id, with_for_update=True)
        if player is None:
            raise ValueError("Player missing")
        player.balance_mamp += amount
        await self.session.flush()
        return amount


async def denomination_to_mamp(denom: Denomination) -> int:
    return DENOMINATION_MULTIPLIER[denom]
