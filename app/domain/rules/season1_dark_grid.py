from __future__ import annotations

import uuid

from app.core import events
from app.domain.rules.base_ruleset import ActionDefinition, ValidationError
from app.domain.rules.registry import registry
from app.domain.services.currency_service import CurrencyService
from app.domain.services.market_service import MarketService


async def validate_work(context, payload):  # type: ignore[override]
    return None


async def apply_work(context, payload):  # type: ignore[override]
    actor_id = context.action.actor_id
    reward = int(payload.get("reward", 100))
    currency = CurrencyService(context.session)
    balance = await currency.adjust_balance(actor_id, reward)
    await events.record_event(
        context.session,
        tick=context.tick,
        kind="action.work",
        subject_id=actor_id,
        payload={"reward": reward, "balance": balance},
    )
    return {"balance": balance}


async def validate_list_item(context, payload):  # type: ignore[override]
    if "item_type" not in payload or "price_amp" not in payload:
        raise ValidationError("item_type and price_amp required")
    price = int(payload["price_amp"])
    if price <= 0:
        raise ValidationError("price must be positive")


async def apply_list_item(context, payload):  # type: ignore[override]
    market = MarketService(context.session)
    listing = await market.create_listing(
        seller_id=context.action.actor_id,
        item_type=str(payload["item_type"]),
        item_attrs=dict(payload.get("item_attrs", {})),
        price_amp=int(payload["price_amp"]),
        tick=context.tick,
    )
    await events.record_event(
        context.session,
        tick=context.tick,
        kind="market.listing_created",
        subject_id=listing.id,
        payload={"item_type": listing.item_type, "price_amp": listing.price_amp_bigint},
    )
    return {"listing_id": str(listing.id)}


async def validate_buy_item(context, payload):  # type: ignore[override]
    if "listing_id" not in payload:
        raise ValidationError("listing_id required")


async def apply_buy_item(context, payload):  # type: ignore[override]
    market = MarketService(context.session)
    listing = await market.buy_listing(
        listing_id=uuid.UUID(str(payload["listing_id"])),
        buyer_id=context.action.actor_id,
        tick=context.tick,
    )
    await events.record_event(
        context.session,
        tick=context.tick,
        kind="market.listing_filled",
        subject_id=listing.id,
        payload={"buyer_id": str(context.action.actor_id)},
    )
    return {"listing_id": str(listing.id)}


async def validate_cancel_listing(context, payload):  # type: ignore[override]
    if "listing_id" not in payload:
        raise ValidationError("listing_id required")


async def apply_cancel_listing(context, payload):  # type: ignore[override]
    market = MarketService(context.session)
    listing = await market.cancel_listing(
        listing_id=uuid.UUID(str(payload["listing_id"])),
        actor_id=context.action.actor_id,
        tick=context.tick,
    )
    await events.record_event(
        context.session,
        tick=context.tick,
        kind="market.listing_cancelled",
        subject_id=listing.id,
        payload={},
    )
    return {"listing_id": str(listing.id)}


registry.register_action(ActionDefinition("work", validate_work, apply_work))
registry.register_action(ActionDefinition("list_item", validate_list_item, apply_list_item))
registry.register_action(ActionDefinition("buy_item", validate_buy_item, apply_buy_item))
registry.register_action(
    ActionDefinition("cancel_listing", validate_cancel_listing, apply_cancel_listing)
)
