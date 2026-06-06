# FactoryPulse Assistant

A small FastAPI service that answers natural-language questions about the shop
floor — *"What's DB-01's OEE this week?"*, *"Which machine lost the most time
to stoppages today?"* — by running an **agentic loop** with Claude's tool-use
(function calling) feature against FactoryPulse's read-only analytics API.

```
POST /ask
{ "question": "How is the painting line doing today?" }

200 OK
{ "answer": "DB-01 (Painting Robot) is at 78% OEE over the last 24h..." }
```

## How it works

1. The question is sent to Claude together with a catalogue of tools
   (`list_machines`, `get_oee`, `get_downtime`, `top_downtime`).
2. When Claude responds with `stop_reason == "tool_use"`, each requested tool
   call is executed and the result is sent back as a `tool_result` block.
3. This repeats — Claude can chain multiple calls (e.g. `list_machines` to
   resolve a name to a `device_id`, then `get_oee` for that id) — until it
   replies in plain text, or a small step budget is reached.

`factorypulse_assistant/agent.py` (`FactoryPulseAgent.ask`) implements this
loop; `factorypulse_assistant/tools.py` declares the tool schemas in the shape
the Claude API expects and dispatches calls by name.

## Sharing the FactoryPulse client with the MCP server

This service does **not** reimplement the FactoryPulse API integration. It
depends on `factorypulse-mcp` (installed as a local editable package — see
its `pyproject.toml`) and reuses `factorypulse_mcp.client.FactoryPulseClient`
directly: the same authenticated, read-only HTTP client that backs the MCP
tools in Phase 2. `ToolDispatcher` in `tools.py` is the only new integration
code — a thin adapter from "Claude wants to call tool X with arguments Y" to
"call this method on the shared client".

Two delivery mechanisms (an MCP server for MCP-compatible clients like Claude
Desktop, and this HTTP agent for the React frontend), one FactoryPulse
integration.

## Configuration

Copy `.env.example` to `.env` and fill it in:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `FACTORYPULSE_API` | Base URL of the FactoryPulse REST API, e.g. `http://localhost:8000/api` |
| `FACTORYPULSE_TOKEN` | Read-only JWT from `create_service_token` (never commit this) |
| `ANTHROPIC_API_KEY` | API key used to call Claude (never commit this) |
| `ANTHROPIC_MODEL` | Claude model id used for tool-calling (default `claude-sonnet-4-6`) |
| `CORS_ALLOW_ORIGINS` | Comma-separated origins allowed to call `/ask` from a browser, e.g. the React dev server |

## Setup

```bash
cd factorypulse-assistant
python -m venv venv
./venv/Scripts/activate          # Windows — use `source venv/bin/activate` on Linux/macOS
pip install -e ../factorypulse-mcp
pip install -e ".[dev]"
cp .env.example .env             # then edit ANTHROPIC_API_KEY and FACTORYPULSE_TOKEN
```

## Running it

```bash
uvicorn factorypulse_assistant.main:app --reload --port 8001
```

```bash
curl -X POST http://localhost:8001/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is DB-01 OEE in the last 7 days?"}'
```

## Running with Docker

Build from the **repository root** so the image can also pick up the
`factorypulse-mcp` package it depends on:

```bash
docker build -f factorypulse-assistant/Dockerfile -t factorypulse-assistant .
docker run --rm -p 8001:8001 \
  -e FACTORYPULSE_API=http://host.docker.internal:8000/api \
  -e FACTORYPULSE_TOKEN=<token> \
  -e ANTHROPIC_API_KEY=<key> \
  factorypulse-assistant
```

## Tests

```bash
pytest
```

Everything is exercised through fakes/doubles — a fake Anthropic client and a
fake tool dispatcher for the agent loop, a fake `FactoryPulseClient` for the
dispatcher, and a FastAPI dependency override (fake agent) for the `/ask`
endpoint — so the suite needs no API key, no live FactoryPulse instance and
makes no network calls.
