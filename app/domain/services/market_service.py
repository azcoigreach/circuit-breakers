from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import models
from app.domain.models import MarketListing, MarketStatus
from app.domain.services.currency_service import CurrencyService


class MarketService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.currency = CurrencyService(session)

    async def create_listing(
        self,
        *,
        seller_id: uuid.UUID,
        item_type: str,
        item_attrs: Dict[str, object],
        price_amp: int,
        tick: int,
    ) -> MarketListing:
        listing = MarketListing(
            seller_id=seller_id,
            item_type=item_type,
            item_attrs=item_attrs,
            price_amp_bigint=price_amp,
            status=MarketStatus.open,
            created_tick=tick,
        )
        self.session.add(listing)
        await self.session.flush()
        return listing

    async def list_listings(
        self,
        *,
        status: Optional[MarketStatus] = None,
        seller_id: Optional[uuid.UUID] = None,
        item_type: Optional[str] = None,
    ) -> List[MarketListing]:
        stmt = select(MarketListing)
        if status is not None:
            stmt = stmt.where(MarketListing.status == status)
        if seller_id is not None:
            stmt = stmt.where(MarketListing.seller_id == seller_id)
        if item_type is not None:
            stmt = stmt.where(MarketListing.item_type == item_type)
        stmt = stmt.order_by(MarketListing.created_tick)
        result = await self.session.execute(stmt)
        return list(result.scalars())

    async def buy_listing(self, *, listing_id: uuid.UUID, buyer_id: uuid.UUID, tick: int) -> MarketListing:
        listing = await self.session.get(MarketListing, listing_id, with_for_update=True)
        if listing is None:
            raise ValueError("Listing not found")
        if listing.status != MarketStatus.open:
            raise ValueError("Listing is not open")
        if listing.seller_id == buyer_id:
            raise ValueError("Cannot buy your own listing")
        await self.currency.transfer(buyer_id, listing.seller_id, int(listing.price_amp_bigint))
        listing.status = MarketStatus.filled
        listing.filled_tick = tick
        await self.session.flush()
        return listing

    async def cancel_listing(self, *, listing_id: uuid.UUID, actor_id: uuid.UUID, tick: int) -> MarketListing:
        listing = await self.session.get(MarketListing, listing_id, with_for_update=True)
        if listing is None:
            raise ValueError("Listing not found")
        if listing.seller_id != actor_id:
            raise ValueError("Only seller can cancel listing")
        if listing.status != MarketStatus.open:
            raise ValueError("Listing not open")
        listing.status = MarketStatus.cancelled
        listing.filled_tick = tick
        await self.session.flush()
        return listing
