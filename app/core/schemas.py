from __future__ import annotations

import uuid
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, Field

from app.domain.models import Denomination, MarketStatus


class WorldState(BaseModel):
    tick: int
    seed: int
    ruleset_version: str


class EntitySchema(BaseModel):
    id: uuid.UUID
    type: str
    owner_id: Optional[uuid.UUID] = None
    pos: Optional[Dict[str, Any]] = None
    attrs: Dict[str, Any] = Field(default_factory=dict)
    version: int


class ActionSchema(BaseModel):
    type: str
    actor_id: uuid.UUID
    payload: Dict[str, Any] = Field(default_factory=dict)


class EnqueueResponse(BaseModel):
    accepted: List[uuid.UUID]
    tick: int


class MarketListingSchema(BaseModel):
    id: uuid.UUID
    seller_id: uuid.UUID
    item_type: str
    item_attrs: Dict[str, Any]
    price_amp: int = Field(alias="price_amp_bigint")
    status: MarketStatus
    created_tick: int
    filled_tick: Optional[int] = None

    class Config:
        populate_by_name = True


class CurrencyPacketSchema(BaseModel):
    id: uuid.UUID
    denom: Denomination
    encrypted: bool
    payload: Dict[str, Any]


class EventSchema(BaseModel):
    id: uuid.UUID
    tick: int
    kind: str
    subject_id: Optional[uuid.UUID] = None
    payload: Dict[str, Any]


class CurrencyMetadataSchema(BaseModel):
    base_unit: str = "mAMP"
    DENOMINATIONS: ClassVar[List[str]] = [denom.value for denom in Denomination]
    denominations: List[str] = Field(default_factory=lambda: CurrencyMetadataSchema.DENOMINATIONS)
    lore: str = (
        "AMPs are Anonymous Market Packets—energy siphoned from megacorps and hashed into currency."
    )


class BalanceSchema(BaseModel):
    balance_mamp: int


class TransferRequest(BaseModel):
    recipient_id: uuid.UUID
    amount_mamp: int


class DecryptRequest(BaseModel):
    packet_id: uuid.UUID
    solution: Dict[str, Any]


class ActionSubmission(BaseModel):
    actions: List[ActionSchema]


class MarketCreateRequest(BaseModel):
    item_type: str
    item_attrs: Dict[str, Any] = Field(default_factory=dict)
    price_amp: int


class MarketFilter(BaseModel):
    status: Optional[MarketStatus] = None
    seller_id: Optional[uuid.UUID] = None
    item_type: Optional[str] = None


class CurrencyTransferPayload(BaseModel):
    recipient_id: uuid.UUID
    amount_mamp: int


class CurrencyMintRequest(BaseModel):
    denom: Denomination
    payload: Dict[str, Any] = Field(default_factory=dict)
