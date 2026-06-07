"""
FastMCP server exposing FactoryPulse's read-only OEE/downtime analytics as
tools an LLM can call directly: list_machines, get_oee, get_downtime and
top_downtime.

Local development / Claude Desktop (stdio transport):
    python -m factorypulse_mcp.server

Interactive inspection with the MCP Inspector:
    mcp dev factorypulse_mcp/server.py
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import FactoryPulseClient
from .config import load_settings

settings = load_settings()
client = FactoryPulseClient(settings.api_base_url, settings.token)

mcp = FastMCP("FactoryPulse", host=settings.host, port=settings.port)


@mcp.tool()
async def list_machines() -> list[dict[str, Any]]:
    """
    List every machine registered in FactoryPulse: device id, name, type,
    ideal cycle time and its current OEE snapshot.

    Call this first to discover valid `machine_id` values (the `device_id`,
    e.g. "DB-01") for get_oee, get_downtime and top_downtime.
    """
    return await client.list_machines()


@mcp.tool()
async def get_oee(machine_id: str, period: str = "24h") -> dict[str, Any]:
    """
    Get the OEE breakdown for one machine over a time window: Availability,
    Performance, Quality and the global OEE score (percentages, 0-100).

    Args:
        machine_id: The machine's device_id, e.g. "DB-01" (see list_machines).
        period: Rolling time window ending now — "30m", "24h", "7d", "30d", etc.
    """
    return await client.get_oee(machine_id, period)


@mcp.tool()
async def get_downtime(machine_id: str, period: str = "24h") -> dict[str, Any]:
    """
    List stoppages recorded for one machine over a time window. Each entry
    has a start timestamp, an end timestamp (or null with "ongoing": true for
    a stoppage still in progress) and its duration in seconds, plus totals
    for the whole period.

    Args:
        machine_id: The machine's device_id, e.g. "DB-01" (see list_machines).
        period: Rolling time window ending now — "30m", "24h", "7d", "30d", etc.
    """
    return await client.get_downtime(machine_id, period)


@mcp.tool()
async def top_downtime(period: str = "24h", limit: int = 5) -> dict[str, Any]:
    """
    Rank machines by total downtime within a time window — the fastest way to
    answer "which machine is losing the most production time right now?".

    Args:
        period: Rolling time window ending now — "30m", "24h", "7d", "30d", etc.
        limit: Maximum number of machines to return (1-50, default 5).
    """
    return await client.top_downtime(period, limit)


def main() -> None:
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
