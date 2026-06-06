"""
Tests that each MCP tool delegates to the FactoryPulseClient with the right
arguments and returns its result untouched — no network or live API needed.
The HTTP behaviour itself is covered in test_client.py.
"""
import asyncio

import pytest

from factorypulse_mcp import server


class FakeClient:
    def __init__(self):
        self.calls = []

    async def list_machines(self):
        self.calls.append(("list_machines",))
        return [{"device_id": "DB-01"}]

    async def get_oee(self, machine_id, period):
        self.calls.append(("get_oee", machine_id, period))
        return {"oee": {"global": 80.0}}

    async def get_downtime(self, machine_id, period):
        self.calls.append(("get_downtime", machine_id, period))
        return {"stoppage_count": 0, "stoppages": []}

    async def top_downtime(self, period, limit):
        self.calls.append(("top_downtime", period, limit))
        return {"ranking": []}


@pytest.fixture
def fake_client(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(server, "client", fake)
    return fake


def test_list_machines_delegates_to_client(fake_client):
    result = asyncio.run(server.list_machines())

    assert result == [{"device_id": "DB-01"}]
    assert fake_client.calls == [("list_machines",)]


def test_get_oee_passes_machine_id_and_period(fake_client):
    result = asyncio.run(server.get_oee("DB-01", "7d"))

    assert result == {"oee": {"global": 80.0}}
    assert fake_client.calls == [("get_oee", "DB-01", "7d")]


def test_get_oee_defaults_period_to_24h(fake_client):
    asyncio.run(server.get_oee("DB-01"))

    assert fake_client.calls == [("get_oee", "DB-01", "24h")]


def test_get_downtime_passes_machine_id_and_period(fake_client):
    result = asyncio.run(server.get_downtime("RB-02", "30d"))

    assert result == {"stoppage_count": 0, "stoppages": []}
    assert fake_client.calls == [("get_downtime", "RB-02", "30d")]


def test_top_downtime_passes_period_and_limit(fake_client):
    result = asyncio.run(server.top_downtime("7d", 3))

    assert result == {"ranking": []}
    assert fake_client.calls == [("top_downtime", "7d", 3)]


def test_top_downtime_uses_defaults_when_omitted(fake_client):
    asyncio.run(server.top_downtime())

    assert fake_client.calls == [("top_downtime", "24h", 5)]


def test_tools_are_registered_with_descriptive_docstrings():
    tools = asyncio.run(server.mcp.list_tools())
    tools_by_name = {tool.name: tool for tool in tools}

    assert set(tools_by_name) == {"list_machines", "get_oee", "get_downtime", "top_downtime"}
    for tool in tools_by_name.values():
        assert tool.description, f"{tool.name} is missing a docstring/description"
