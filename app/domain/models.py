from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


json_variant = JSON().with_variant(JSONB, "postgresql")


class World(Base):
    __tablename__ = "world"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    tick: Mapped[int] = mapped_column(Integer, default=0)
    seed: Mapped[int] = mapped_column(Integer, default=1337)
    ruleset_version: Mapped[str] = mapped_column(String(64), default="season1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Player(Base):
    __tablename__ = "player"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    handle: Mapped[str] = mapped_column(String(64), unique=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    balance_mamp: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Entity(Base):
    __tablename__ = "entity"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    type: Mapped[str] = mapped_column(String(64))
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("player.id"), nullable=True
    )
    pos: Mapped[Optional[Dict[str, Any]]] = mapped_column(json_variant, nullable=True)
    attrs: Mapped[Dict[str, Any]] = mapped_column(json_variant, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    owner: Mapped[Optional[Player]] = relationship(Player)


class MarketStatus(str, enum.Enum):
    pending = "pending"
    open = "open"
    filled = "filled"
    cancelled = "cancelled"


class MarketListing(Base):
    __tablename__ = "market_listing"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id"))
    item_type: Mapped[str] = mapped_column(String(64))
    item_attrs: Mapped[Dict[str, Any]] = mapped_column(json_variant, default=dict)
    price_amp_bigint: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[MarketStatus] = mapped_column(Enum(MarketStatus), default=MarketStatus.pending)
    created_tick: Mapped[int] = mapped_column(Integer)
    filled_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    seller: Mapped[Player] = relationship(Player)


class Action(Base):
    __tablename__ = "action"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    tick: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id"))
    type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[Dict[str, Any]] = mapped_column(json_variant, default=dict)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    signature: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    actor: Mapped[Player] = relationship(Player)


class Event(Base):
    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    tick: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(64))
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(json_variant, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Denomination(str, enum.Enum):
    mAMP = "mAMP"
    kAMP = "kAMP"
    MAMP = "MAMP"
    GAMP = "GAMP"


class CurrencyPacket(Base):
    __tablename__ = "currency_packet"

    id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, primary_key=True)
    denom: Mapped[Denomination] = mapped_column(Enum(Denomination))
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(json_variant, default=dict)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("player.id"))
    created_tick: Mapped[int] = mapped_column(Integer)
    owner: Mapped[Player] = relationship(Player)


class ReplayLog(Base):
    __tablename__ = "replay_log"

    tick: Mapped[int] = mapped_column(Integer, primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(64))
    prev_hash: Mapped[str] = mapped_column(String(64))
    actions: Mapped[Dict[str, Any]] = mapped_column(json_variant, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


__all__ = [
    "Action",
    "CurrencyPacket",
    "Denomination",
    "Entity",
    "Event",
    "MarketListing",
    "MarketStatus",
    "Player",
    "ReplayLog",
    "World",
    "Base",
]
