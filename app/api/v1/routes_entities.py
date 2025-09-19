from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import schemas
from app.domain import models
from app.infra.db import get_session

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("/", response_model=List[schemas.EntitySchema])
async def list_entities(
    owner_id: Optional[uuid.UUID] = Query(default=None),
    type: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> List[schemas.EntitySchema]:
    stmt = select(models.Entity)
    if owner_id is not None:
        stmt = stmt.where(models.Entity.owner_id == owner_id)
    if type is not None:
        stmt = stmt.where(models.Entity.type == type)
    result = await session.execute(stmt)
    entities = result.scalars().all()
    return [
        schemas.EntitySchema(
            id=entity.id,
            type=entity.type,
            owner_id=entity.owner_id,
            pos=entity.pos,
            attrs=entity.attrs,
            version=entity.version,
        )
        for entity in entities
    ]


@router.get("/{entity_id}", response_model=schemas.EntitySchema)
async def get_entity(
    entity_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> schemas.EntitySchema:
    entity = await session.get(models.Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return schemas.EntitySchema(
        id=entity.id,
        type=entity.type,
        owner_id=entity.owner_id,
        pos=entity.pos,
        attrs=entity.attrs,
        version=entity.version,
    )
