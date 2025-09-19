from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.core.ticks import TickManager
from app.domain.models import MarketStatus
from app.domain.services.market_service import MarketService
from app.infra.db import lifespan_session

app = FastAPI(title="Circuit Breakers MCP")


ToolHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


async def handle_get_world_state(_: Dict[str, Any]) -> Dict[str, Any]:
    async with lifespan_session() as session:
        manager = TickManager(session)
        world = await manager.get_world_state()
        return {"tick": world.tick, "seed": world.seed, "ruleset_version": world.ruleset_version}


async def handle_list_market_listings(params: Dict[str, Any]) -> Dict[str, Any]:
    async with lifespan_session() as session:
        market = MarketService(session)
        status_value = params.get("status")
        status = MarketStatus(status_value) if status_value else None
        listings = await market.list_listings(
            status=status,
            seller_id=params.get("seller_id"),
            item_type=params.get("item_type"),
        )
        return {"listings": [
            {
                "id": str(listing.id),
                "item_type": listing.item_type,
                "price_amp": int(listing.price_amp_bigint),
                "status": listing.status.value,
            }
            for listing in listings
        ]}


async def handle_subscribe_events(_: Dict[str, Any]) -> Dict[str, Any]:
    return {"subscription": "events"}


tool_map: Dict[str, ToolHandler] = {
    "get_world_state": handle_get_world_state,
    "list_market_listings": handle_list_market_listings,
    "subscribe_events": handle_subscribe_events,
}


@app.websocket("/mcp")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            payload = json.loads(message)
            tool = payload.get("tool")
            params = payload.get("params", {})
            handler = tool_map.get(tool)
            if handler is None:
                await websocket.send_text(json.dumps({"error": f"unknown tool {tool}"}))
                continue
            result = await handler(params)
            await websocket.send_text(json.dumps({"tool": tool, "result": result}))
    except WebSocketDisconnect:
        return
