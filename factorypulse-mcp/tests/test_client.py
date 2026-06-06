import asyncio

import httpx
import pytest

from factorypulse_mcp.client import FactoryPulseClient
from factorypulse_mcp.config import Settings


def _settings(token="service-token"):
    return Settings(
        api_base_url="http://testserver/api",
        token=token,
        transport="stdio",
        host="127.0.0.1",
        port=8000,
    )


def _client_with(handler, token="service-token"):
    return FactoryPulseClient(_settings(token), transport=httpx.MockTransport(handler))


def test_attaches_bearer_token_from_settings():
    seen = {}

    def handler(request):
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json=[])

    asyncio.run(_client_with(handler).list_machines())

    assert seen["authorization"] == "Bearer service-token"


def test_omits_authorization_header_when_token_is_missing():
    seen = {}

    def handler(request):
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json=[])

    asyncio.run(_client_with(handler, token=None).list_machines())

    assert seen["authorization"] is None


def test_list_machines_hits_expected_path_and_returns_json():
    def handler(request):
        assert request.url.path == "/api/machines/"
        return httpx.Response(200, json=[{"device_id": "DB-01"}])

    result = asyncio.run(_client_with(handler).list_machines())

    assert result == [{"device_id": "DB-01"}]


def test_get_oee_forwards_machine_id_and_period():
    def handler(request):
        assert request.url.path == "/api/machines/DB-01/oee/"
        assert request.url.params["period"] == "7d"
        return httpx.Response(200, json={"oee": {"global": 80.0}})

    result = asyncio.run(_client_with(handler).get_oee("DB-01", "7d"))

    assert result == {"oee": {"global": 80.0}}


def test_get_downtime_forwards_machine_id_and_period():
    def handler(request):
        assert request.url.path == "/api/machines/RB-02/downtime/"
        assert request.url.params["period"] == "24h"
        return httpx.Response(200, json={"stoppage_count": 1})

    result = asyncio.run(_client_with(handler).get_downtime("RB-02", "24h"))

    assert result == {"stoppage_count": 1}


def test_top_downtime_forwards_period_and_limit():
    def handler(request):
        assert request.url.path == "/api/downtime/top/"
        assert request.url.params["period"] == "7d"
        assert request.url.params["limit"] == "3"
        return httpx.Response(200, json={"ranking": []})

    result = asyncio.run(_client_with(handler).top_downtime("7d", 3))

    assert result == {"ranking": []}


def test_raises_for_http_error_status():
    def handler(request):
        return httpx.Response(404, json={"detail": "Not found"})

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(_client_with(handler).get_oee("UNKNOWN", "24h"))
