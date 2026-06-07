"""
Wires the real collaborators together: FactoryPulseAgent -> ToolDispatcher ->
FactoryPulseClient -> httpx — and exercises a realistic multi-tool
conversation end to end.

test_agent.py and test_tools.py each prove their unit's contract against a
fake neighbour (FakeDispatcher / FakeClient respectively); neither catches a
mismatch *between* them — e.g. ToolDispatcher passing an argument
FactoryPulseClient doesn't accept, or building a URL the live API wouldn't
recognise. This suite closes that gap by assembling the production chain for
real and doubling only the two boundaries that need a live network/API key:
the Gemini client (FakeGenAIClient, as in test_agent.py, built from real
`google.genai.types` response shapes) and the HTTP transport underneath
FactoryPulseClient (httpx.MockTransport, as in factorypulse-mcp's
test_client.py — the same client, the same technique).
"""
import asyncio

import httpx
from google.genai import types

from factorypulse_mcp.client import FactoryPulseClient

from factorypulse_assistant.agent import FactoryPulseAgent
from factorypulse_assistant.tools import ToolDispatcher


def _text_part(text):
    return types.Part.from_text(text=text)


def _call_part(name, **args):
    return types.Part.from_function_call(name=name, args=args)


def _model_response(*parts):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=list(parts)),
                finish_reason=types.FinishReason.STOP,
            )
        ]
    )


class FakeAsyncModels:
    def __init__(self, responses):
        self._responses = list(responses)

    async def generate_content(self, **kwargs):
        return self._responses.pop(0)


class FakeAio:
    def __init__(self, responses):
        self.models = FakeAsyncModels(responses)


class FakeGenAIClient:
    def __init__(self, responses):
        self.aio = FakeAio(responses)


# Stand-ins for the JSON the real FactoryPulse API returns for these exact
# routes — shaped like the payloads core/serializers.py and core/analytics.py
# produce, so a route/shape mismatch between ToolDispatcher and
# FactoryPulseClient would surface here rather than only in production.
TOP_DOWNTIME_RESPONSE = {
    "ranking": [
        {"machine": "CNC-03", "total_downtime_seconds": 22348.0, "stoppage_count": 21},
        {"machine": "DB-01", "total_downtime_seconds": 11758.0, "stoppage_count": 14},
    ]
}
CNC_OEE_RESPONSE = {
    "oee": {"availability": 99.0, "performance": 71.7, "quality": 95.0, "global": 67.4}
}


def _build_agent(responses):
    """
    Assembles the real FactoryPulseAgent -> ToolDispatcher -> FactoryPulseClient
    chain over a recording httpx.MockTransport, returning the agent plus the
    list of requests the client actually issued — the evidence that the chain
    is wired correctly, not just that each link works in isolation.
    """
    requests: list[httpx.Request] = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/api/downtime/top/":
            assert request.url.params["period"] == "7d"
            return httpx.Response(200, json=TOP_DOWNTIME_RESPONSE)
        if request.url.path == "/api/machines/CNC-03/oee/":
            assert request.url.params["period"] == "7d"
            return httpx.Response(200, json=CNC_OEE_RESPONSE)
        return httpx.Response(404, json={"detail": "unexpected request in test"})

    client = FactoryPulseClient("http://testserver/api", "service-token", transport=httpx.MockTransport(handler))
    agent = FactoryPulseAgent(FakeGenAIClient(responses), ToolDispatcher(client), model="gemini-2.5-flash")
    return agent, requests


def test_agent_answers_a_two_tool_question_through_the_real_client_and_dispatcher():
    responses = [
        _model_response(_call_part("top_downtime", period="7d", limit=3)),
        _model_response(_call_part("get_oee", machine_id="CNC-03", period="7d")),
        _model_response(_text_part(
            "CNC-03 lost the most time to stoppages this week (about 6.2 hours) "
            "and is running at 67.4% OEE — the one to focus on."
        )),
    ]

    agent, requests = _build_agent(responses)
    answer = asyncio.run(agent.ask("Which machine needs the most attention this week, and what's its OEE?"))

    assert "CNC-03" in answer
    assert "67.4" in answer

    # The real client must have produced exactly the HTTP calls a live
    # FactoryPulse API expects — correct paths, params and auth header —
    # proving the dispatcher -> client boundary is wired correctly end to end.
    assert [request.url.path for request in requests] == [
        "/api/downtime/top/",
        "/api/machines/CNC-03/oee/",
    ]
    assert all(request.headers["authorization"] == "Bearer service-token" for request in requests)


def test_agent_surfaces_a_real_http_error_from_the_client_as_a_function_error():
    responses = [
        _model_response(_call_part("get_oee", machine_id="GHOST-99", period="24h")),
        _model_response(_text_part("I couldn't find a machine called GHOST-99.")),
    ]

    def handler(request):
        return httpx.Response(404, json={"detail": "Not found."})

    client = FactoryPulseClient("http://testserver/api", "service-token", transport=httpx.MockTransport(handler))
    agent = FactoryPulseAgent(FakeGenAIClient(responses), ToolDispatcher(client), model="gemini-2.5-flash")

    answer = asyncio.run(agent.ask("What's GHOST-99's OEE?"))

    assert answer == "I couldn't find a machine called GHOST-99."
