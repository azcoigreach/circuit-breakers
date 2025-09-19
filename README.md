# Circuit Breakers – Season 1: The Dark Grid

Circuit Breakers is a deterministic, headless cyberpunk market engine. Players and AIs interact exclusively through the API surface (REST + WebSocket + MCP). Season 1 focuses on the Dark Grid market, AMPs, and deterministic replay.

## Features

- FastAPI application with REST and WebSocket endpoints
- Deterministic tick loop with hash-chained replay logs
- AMPs (Anonymous Market Packets) with both liquid balances and encrypted packets
- Season 1 ruleset for listing, buying, and cancelling market commodities
- Structured logging with request correlation
- MCP adapter exposing core tools for agents
- Docker + docker-compose for local development

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
make dev
```

The API will be available at `http://localhost:8000/v1`. Interactive docs live at `/docs`.

### Docker Compose

```bash
docker-compose up --build
```

This launches the API, PostgreSQL, and Redis containers.

## API Overview

### Authentication

All gameplay endpoints expect a Personal Access Token:

```
Authorization: Bearer <token>
```

### REST Examples

```bash
# Fetch world state
curl http://localhost:8000/v1/world/

# Submit a work action
curl -X POST http://localhost:8000/v1/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"actions":[{"type":"work","actor_id":"$PLAYER_ID","payload":{"reward":250}}]}'

# Create a market listing
curl -X POST http://localhost:8000/v1/market/listings \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"item_type":"raw-data","price_amp":1500}'
```

### WebSocket Stream

```python
import asyncio
import websockets
import json

async def listen():
    async with websockets.connect("ws://localhost:8000/v1/ws") as ws:
        while True:
            message = await ws.recv()
            payload = json.loads(message)
            print(payload)

asyncio.run(listen())
```

## Testing

```bash
make test
```

Targets 80% coverage via `pytest --cov`.

## MCP Adapter

The MCP adapter exposes the same primitives for LLM agents. Launch it with Uvicorn:

```bash
uvicorn app.mcp.server:app --host 0.0.0.0 --port 9000
```

## Project Layout

```
app/
  api/v1/        # FastAPI routers
  core/          # config, logging, ticks, replay
  domain/        # SQLAlchemy models, rules, services
  infra/         # database + migrations
  mcp/           # MCP manifest + server
  app.py         # FastAPI application factory
```

## License

Released under the MIT License. See [LICENSE](LICENSE).
