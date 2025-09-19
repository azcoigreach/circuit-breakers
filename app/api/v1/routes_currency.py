from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.core.auth import authenticate_token
from app.core.config import get_settings
from app.core.ticks import TickManager
from app.domain.services.currency_service import CurrencyService
from app.infra.db import get_session

router = APIRouter(prefix="/currency", tags=["currency"])


@router.get("/", response_model=schemas.CurrencyMetadataSchema)
async def metadata() -> schemas.CurrencyMetadataSchema:
    return schemas.CurrencyMetadataSchema()


@router.get("/balance", response_model=schemas.BalanceSchema)
async def balance(
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.BalanceSchema:
    service = CurrencyService(session)
    amount = await service.get_balance(player.id)
    return schemas.BalanceSchema(balance_mamp=amount)


@router.post("/transfer")
async def transfer(
    payload: schemas.TransferRequest,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.BalanceSchema:
    service = CurrencyService(session)
    try:
        await service.transfer(player.id, payload.recipient_id, payload.amount_mamp)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    balance = await service.get_balance(player.id)
    return schemas.BalanceSchema(balance_mamp=balance)


@router.post("/mint_encrypted", response_model=schemas.CurrencyPacketSchema)
async def mint_encrypted(
    payload: schemas.CurrencyMintRequest,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.CurrencyPacketSchema:
    settings = get_settings()
    if not settings.dev_mode:
        raise HTTPException(status_code=403, detail="mint disabled")
    manager = TickManager(session)
    world = await manager.get_world_state()
    service = CurrencyService(session)
    packet = await service.mint_encrypted_packet(
        owner_id=player.id,
        denom=payload.denom,
        payload=payload.payload,
        created_tick=world.tick,
    )
    return schemas.CurrencyPacketSchema.model_validate(packet)


@router.get("/packets", response_model=List[schemas.CurrencyPacketSchema])
async def list_packets(
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> List[schemas.CurrencyPacketSchema]:
    service = CurrencyService(session)
    packets = await service.list_packets(player.id)
    return [schemas.CurrencyPacketSchema.model_validate(packet) for packet in packets]


@router.post("/decrypt")
async def decrypt(
    payload: schemas.DecryptRequest,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.BalanceSchema:
    service = CurrencyService(session)
    try:
        reward = await service.decrypt_packet(player.id, payload.packet_id, payload.solution)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    balance = await service.get_balance(player.id)
    return schemas.BalanceSchema(balance_mamp=balance)
