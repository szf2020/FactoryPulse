"""
Tool catalogue and dispatcher for the assistant's agentic loop.

`TOOL_DEFINITIONS` describes the same FactoryPulse analytics operations
exposed as MCP tools in `factorypulse_mcp.server` — list machines, OEE,
downtime and the downtime ranking — but in the JSON-schema shape the Claude
API's tool-use feature expects. `ToolDispatcher` then executes a tool call by
name through `FactoryPulseClient`, the very same read-only API integration the
MCP server uses, so both delivery mechanisms (MCP and this HTTP agent) share
one FactoryPulse domain client instead of duplicating it.
"""
from __future__ import annotations

from typing import Any

from factorypulse_mcp.client import FactoryPulseClient

PERIOD_PROPERTY = {
    "type": "string",
    "description": (
        "Rolling time window ending now, e.g. \"30m\", \"24h\", \"7d\", \"30d\". "
        "Defaults to \"24h\" when omitted."
    ),
}

MACHINE_ID_PROPERTY = {
    "type": "string",
    "description": "The machine's device_id, e.g. \"DB-01\" (see list_machines).",
}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "list_machines",
        "description": (
            "List every machine registered in FactoryPulse: device id, name, "
            "type, ideal cycle time and its current OEE snapshot. Call this "
            "first to discover valid machine_id values for the other tools."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_oee",
        "description": (
            "Get the OEE breakdown for one machine over a time window: "
            "Availability, Performance, Quality and the global OEE score "
            "(percentages, 0-100)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "machine_id": MACHINE_ID_PROPERTY,
                "period": PERIOD_PROPERTY,
            },
            "required": ["machine_id"],
        },
    },
    {
        "name": "get_downtime",
        "description": (
            "List stoppages recorded for one machine over a time window. Each "
            "entry has a start timestamp, an end timestamp (or null with "
            "\"ongoing\": true for a stoppage still in progress) and its "
            "duration in seconds, plus totals for the whole period."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "machine_id": MACHINE_ID_PROPERTY,
                "period": PERIOD_PROPERTY,
            },
            "required": ["machine_id"],
        },
    },
    {
        "name": "top_downtime",
        "description": (
            "Rank machines by total downtime within a time window — the "
            "fastest way to answer \"which machine is losing the most "
            "production time right now?\"."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": PERIOD_PROPERTY,
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of machines to return (1-50, default 5).",
                },
            },
        },
    },
]


class UnknownToolError(Exception):
    """Raised when the model asks to call a tool that isn't in the catalogue."""

    def __init__(self, name: str):
        super().__init__(f"Unknown tool: {name}")
        self.name = name


class ToolDispatcher:
    """Executes a named tool call against FactoryPulse's read-only API.

    Wraps `FactoryPulseClient` — the same client `factorypulse_mcp` uses —
    behind a single `dispatch(name, arguments)` entry point, which is exactly
    the shape the agentic loop needs to turn a `tool_use` block into a result.
    """

    def __init__(self, client: FactoryPulseClient):
        self._client = client
        self._handlers = {
            "list_machines": self._list_machines,
            "get_oee": self._get_oee,
            "get_downtime": self._get_downtime,
            "top_downtime": self._top_downtime,
        }

    async def dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        handler = self._handlers.get(name)
        if handler is None:
            raise UnknownToolError(name)
        return await handler(**arguments)

    async def _list_machines(self) -> Any:
        return await self._client.list_machines()

    async def _get_oee(self, machine_id: str, period: str = "24h") -> Any:
        return await self._client.get_oee(machine_id, period)

    async def _get_downtime(self, machine_id: str, period: str = "24h") -> Any:
        return await self._client.get_downtime(machine_id, period)

    async def _top_downtime(self, period: str = "24h", limit: int = 5) -> Any:
        return await self._client.top_downtime(period, limit)
