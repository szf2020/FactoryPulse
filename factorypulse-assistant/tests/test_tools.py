"""
Verifies the tool catalogue is well-formed and that ToolDispatcher routes each
named call to the right FactoryPulseClient method with the right arguments —
no network or live API needed (that's covered in factorypulse-mcp's own
test_client.py, since the client is shared).
"""
import asyncio

import pytest

from factorypulse_assistant.tools import TOOL_DEFINITIONS, ToolDispatcher, UnknownToolError


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
def dispatcher():
    return ToolDispatcher(FakeClient())


def _client_of(dispatcher):
    return dispatcher._client  # the FakeClient — inspected to assert delegation


def test_tool_definitions_expose_name_description_and_schema():
    assert {tool["name"] for tool in TOOL_DEFINITIONS} == {
        "list_machines",
        "get_oee",
        "get_downtime",
        "top_downtime",
    }
    for tool in TOOL_DEFINITIONS:
        assert tool["description"], f"{tool['name']} is missing a description"
        assert tool["input_schema"]["type"] == "object"


def test_get_oee_and_get_downtime_require_machine_id():
    by_name = {tool["name"]: tool for tool in TOOL_DEFINITIONS}

    assert by_name["get_oee"]["input_schema"]["required"] == ["machine_id"]
    assert by_name["get_downtime"]["input_schema"]["required"] == ["machine_id"]


def test_dispatch_list_machines(dispatcher):
    result = asyncio.run(dispatcher.dispatch("list_machines", {}))

    assert result == [{"device_id": "DB-01"}]
    assert _client_of(dispatcher).calls == [("list_machines",)]


def test_dispatch_get_oee_passes_arguments_through(dispatcher):
    result = asyncio.run(dispatcher.dispatch("get_oee", {"machine_id": "DB-01", "period": "7d"}))

    assert result == {"oee": {"global": 80.0}}
    assert _client_of(dispatcher).calls == [("get_oee", "DB-01", "7d")]


def test_dispatch_get_oee_defaults_period(dispatcher):
    asyncio.run(dispatcher.dispatch("get_oee", {"machine_id": "DB-01"}))

    assert _client_of(dispatcher).calls == [("get_oee", "DB-01", "24h")]


def test_dispatch_get_downtime_passes_arguments_through(dispatcher):
    result = asyncio.run(dispatcher.dispatch("get_downtime", {"machine_id": "RB-02", "period": "30d"}))

    assert result == {"stoppage_count": 0, "stoppages": []}
    assert _client_of(dispatcher).calls == [("get_downtime", "RB-02", "30d")]


def test_dispatch_top_downtime_passes_arguments_through(dispatcher):
    result = asyncio.run(dispatcher.dispatch("top_downtime", {"period": "7d", "limit": 3}))

    assert result == {"ranking": []}
    assert _client_of(dispatcher).calls == [("top_downtime", "7d", 3)]


def test_dispatch_top_downtime_uses_defaults_when_omitted(dispatcher):
    asyncio.run(dispatcher.dispatch("top_downtime", {}))

    assert _client_of(dispatcher).calls == [("top_downtime", "24h", 5)]


def test_dispatch_unknown_tool_raises(dispatcher):
    with pytest.raises(UnknownToolError) as excinfo:
        asyncio.run(dispatcher.dispatch("delete_machine", {}))

    assert excinfo.value.name == "delete_machine"
