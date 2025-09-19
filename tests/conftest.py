from __future__ import annotations

import asyncio
import os
from typing import Callable

import pytest
from fastapi.testclient import TestClient

from app.app import create_app
from app.core.auth import hash_token
from app.core.config import get_settings
from app.domain import models
from app.infra.db import drop_db, init_db, lifespan_session

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session", autouse=True)
def configure_env():
    os.environ["APP_ENV"] = "test"
    os.environ["TEST_DATABASE_URL"] = TEST_DB_URL
    os.environ["DEV_MODE"] = "true"
    get_settings.cache_clear()  # type: ignore[attr-defined]
    asyncio.run(drop_db())
    asyncio.run(init_db())
    yield
    asyncio.run(drop_db())


@pytest.fixture
def app_client():
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def create_player() -> Callable[[str, str, int], models.Player]:
    def _create_player(handle: str, token: str, balance: int = 0) -> models.Player:
        async def _inner() -> models.Player:
            async with lifespan_session() as session:
                player = models.Player(
                    handle=handle,
                    token_hash=await hash_token(token),
                    balance_mamp=balance,
                )
                session.add(player)
                await session.flush()
                await session.refresh(player)
                return player

        return asyncio.run(_inner())

    return _create_player
