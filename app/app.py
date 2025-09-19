from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import (
    routes_actions,
    routes_admin,
    routes_currency,
    routes_entities,
    routes_market,
    routes_stream,
    routes_world,
)
from app.core.config import get_settings
from app.core.logging import bind_request_context, clear_request_context, configure_logging
from app.infra.db import init_db

# Import ruleset to register actions
from app.domain.rules import season1_dark_grid  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(debug=settings.debug)
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Circuit Breakers", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        bind_request_context(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            clear_request_context()

    api_v1 = APIRouter(prefix="/v1")
    api_v1.include_router(routes_world.router)
    api_v1.include_router(routes_entities.router)
    api_v1.include_router(routes_actions.router)
    api_v1.include_router(routes_market.router)
    api_v1.include_router(routes_currency.router)
    api_v1.include_router(routes_admin.router)
    api_v1.include_router(routes_stream.router)

    app.include_router(api_v1)

    @app.get("/healthz")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def ready() -> dict:
        return {"status": "ready"}

    return app
