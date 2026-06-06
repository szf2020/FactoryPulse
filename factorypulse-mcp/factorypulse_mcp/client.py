"""
Thin async HTTP client for FactoryPulse's read-only analytics API.

Isolating the HTTP/auth concerns here keeps the MCP tool functions in
server.py focused on a single job — describing the tool to the LLM and
shaping its response — while this class can be unit-tested with a mocked
transport, with no MCP or network dependency at all.
"""
from __future__ import annotations

from typing import Any

import httpx


class FactoryPulseClient:
    """Authenticated client for the FactoryPulse REST API (read-only usage).

    Authentication follows the project's existing scheme: DRF + SimpleJWT,
    i.e. an `Authorization: Bearer <access_token>` header carrying the
    long-lived token issued by `python manage.py create_service_token`.

    Takes the bare `api_base_url`/`token` values rather than a config object —
    this is the FactoryPulse API integration boundary, and keeping its
    interface to exactly what it needs (Interface Segregation) is what lets
    other services (e.g. `factorypulse-assistant`) depend on it directly
    without pulling in MCP-specific settings such as transport/host/port.
    """

    def __init__(self, api_base_url: str, token: str | None = None, transport: httpx.AsyncBaseTransport | None = None):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        self._client = httpx.AsyncClient(
            base_url=f"{api_base_url}/",
            headers=headers,
            timeout=10.0,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def list_machines(self) -> list[dict[str, Any]]:
        return await self._get("machines/")

    async def get_oee(self, machine_id: str, period: str) -> dict[str, Any]:
        return await self._get(f"machines/{machine_id}/oee/", params={"period": period})

    async def get_downtime(self, machine_id: str, period: str) -> dict[str, Any]:
        return await self._get(f"machines/{machine_id}/downtime/", params={"period": period})

    async def top_downtime(self, period: str, limit: int) -> dict[str, Any]:
        return await self._get("downtime/top/", params={"period": period, "limit": limit})
