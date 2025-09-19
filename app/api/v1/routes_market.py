from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.core.auth import authenticate_token
from app.core.ticks import TickManager
from app.domain.models import MarketStatus
from app.domain.services.market_service import MarketService
from app.infra.db import get_session

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/listings", response_model=schemas.MarketListingSchema)
async def create_listing(
    payload: schemas.MarketCreateRequest,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.MarketListingSchema:
    manager = TickManager(session)
    world = await manager.get_world_state()
    market = MarketService(session)
    listing = await market.create_listing(
        seller_id=player.id,
        item_type=payload.item_type,
        item_attrs=payload.item_attrs,
        price_amp=payload.price_amp,
        tick=world.tick,
    )
    return schemas.MarketListingSchema.model_validate(listing)


@router.get("/listings", response_model=List[schemas.MarketListingSchema])
async def list_listings(
    status: MarketStatus | None = Query(default=None),
    seller_id: uuid.UUID | None = Query(default=None),
    item_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> List[schemas.MarketListingSchema]:
    market = MarketService(session)
    listings = await market.list_listings(
        status=status,
        seller_id=seller_id,
        item_type=item_type,
    )
    return [schemas.MarketListingSchema.model_validate(listing) for listing in listings]


@router.post("/listings/{listing_id}/buy", response_model=schemas.MarketListingSchema)
async def buy_listing(
    listing_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.MarketListingSchema:
    manager = TickManager(session)
    world = await manager.get_world_state()
    market = MarketService(session)
    try:
        listing = await market.buy_listing(
            listing_id=listing_id,
            buyer_id=player.id,
            tick=world.tick,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schemas.MarketListingSchema.model_validate(listing)


@router.post("/listings/{listing_id}/cancel", response_model=schemas.MarketListingSchema)
async def cancel_listing(
    listing_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    player=Depends(authenticate_token),
) -> schemas.MarketListingSchema:
    manager = TickManager(session)
    world = await manager.get_world_state()
    market = MarketService(session)
    try:
        listing = await market.cancel_listing(
            listing_id=listing_id,
            actor_id=player.id,
            tick=world.tick,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schemas.MarketListingSchema.model_validate(listing)
