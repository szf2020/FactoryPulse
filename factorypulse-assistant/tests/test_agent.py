"""
Exercises FactoryPulseAgent's tool-use loop end to end against fakes for both
collaborators (the Anthropic client and the tool dispatcher) — no network, no
API key and no FactoryPulse instance needed.
"""
import asyncio
from dataclasses import dataclass

from factorypulse_assistant.agent import MAX_AGENT_STEPS, FactoryPulseAgent
from factorypulse_assistant.tools import UnknownToolError


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict
    type: str = "tool_use"


@dataclass
class FakeResponse:
    content: list
    stop_reason: str


class FakeMessages:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    async def create(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


class FakeAnthropic:
    def __init__(self, responses):
        self.messages = FakeMessages(responses)


class FakeDispatcher:
    def __init__(self, result=None, error=None):
        self.calls = []
        self._result = result if result is not None else {}
        self._error = error

    async def dispatch(self, name, arguments):
        self.calls.append((name, arguments))
        if self._error is not None:
            raise self._error
        return self._result


def _agent(responses, dispatcher=None, model="claude-sonnet-4-6"):
    return FactoryPulseAgent(FakeAnthropic(responses), dispatcher or FakeDispatcher(), model)


def test_ask_returns_text_when_model_answers_without_tools():
    agent = _agent([FakeResponse(content=[TextBlock("DB-01 is running fine.")], stop_reason="end_turn")])

    answer = asyncio.run(agent.ask("How is DB-01 doing?"))

    assert answer == "DB-01 is running fine."


def test_ask_sends_question_model_and_tool_catalogue(monkeypatch):
    anthropic = FakeAnthropic([FakeResponse(content=[TextBlock("ok")], stop_reason="end_turn")])
    agent = FactoryPulseAgent(anthropic, FakeDispatcher(), model="claude-haiku-4-5")

    asyncio.run(agent.ask("ping"))

    request = anthropic.messages.requests[0]
    assert request["model"] == "claude-haiku-4-5"
    assert request["messages"] == [{"role": "user", "content": "ping"}]
    assert {tool["name"] for tool in request["tools"]} >= {"get_oee", "list_machines"}
    assert "FactoryPulse" in request["system"]


def test_ask_executes_requested_tool_and_returns_final_answer():
    tool_use = ToolUseBlock(id="toolu_1", name="get_oee", input={"machine_id": "DB-01", "period": "7d"})
    responses = [
        FakeResponse(content=[tool_use], stop_reason="tool_use"),
        FakeResponse(content=[TextBlock("DB-01's OEE over 7 days is 80%.")], stop_reason="end_turn"),
    ]
    dispatcher = FakeDispatcher(result={"oee": {"global": 80.0}})
    agent = _agent(responses, dispatcher)

    answer = asyncio.run(agent.ask("What's DB-01's OEE this week?"))

    assert answer == "DB-01's OEE over 7 days is 80%."
    assert dispatcher.calls == [("get_oee", {"machine_id": "DB-01", "period": "7d"})]


def test_ask_feeds_tool_result_back_to_the_model():
    tool_use = ToolUseBlock(id="toolu_1", name="get_oee", input={"machine_id": "DB-01"})
    responses = [
        FakeResponse(content=[tool_use], stop_reason="tool_use"),
        FakeResponse(content=[TextBlock("done")], stop_reason="end_turn"),
    ]
    dispatcher = FakeDispatcher(result={"oee": {"global": 80.0}})
    anthropic = FakeAnthropic(responses)
    agent = FactoryPulseAgent(anthropic, dispatcher, "claude-sonnet-4-6")

    asyncio.run(agent.ask("What's DB-01's OEE?"))

    second_request = anthropic.messages.requests[1]
    assert second_request["messages"][1] == {"role": "assistant", "content": [tool_use]}
    tool_result_message = second_request["messages"][2]
    assert tool_result_message["role"] == "user"
    [tool_result] = tool_result_message["content"]
    assert tool_result == {
        "type": "tool_result",
        "tool_use_id": "toolu_1",
        "content": '{"oee": {"global": 80.0}}',
    }


def test_ask_reports_unknown_tool_as_a_tool_error():
    tool_use = ToolUseBlock(id="toolu_1", name="delete_machine", input={})
    responses = [
        FakeResponse(content=[tool_use], stop_reason="tool_use"),
        FakeResponse(content=[TextBlock("I can't do that.")], stop_reason="end_turn"),
    ]
    dispatcher = FakeDispatcher(error=UnknownToolError("delete_machine"))
    anthropic = FakeAnthropic(responses)
    agent = FactoryPulseAgent(anthropic, dispatcher, "claude-sonnet-4-6")

    asyncio.run(agent.ask("Delete DB-01"))

    [tool_result] = anthropic.messages.requests[1]["messages"][2]["content"]
    assert tool_result["is_error"] is True
    assert tool_result["content"] == "Unknown tool: delete_machine"


def test_ask_reports_tool_failures_as_a_tool_error_instead_of_raising():
    tool_use = ToolUseBlock(id="toolu_1", name="get_oee", input={"machine_id": "UNKNOWN"})
    responses = [
        FakeResponse(content=[tool_use], stop_reason="tool_use"),
        FakeResponse(content=[TextBlock("That machine doesn't seem to exist.")], stop_reason="end_turn"),
    ]
    dispatcher = FakeDispatcher(error=RuntimeError("404 Not Found"))
    anthropic = FakeAnthropic(responses)
    agent = FactoryPulseAgent(anthropic, dispatcher, "claude-sonnet-4-6")

    answer = asyncio.run(agent.ask("What's UNKNOWN's OEE?"))

    assert answer == "That machine doesn't seem to exist."
    [tool_result] = anthropic.messages.requests[1]["messages"][2]["content"]
    assert tool_result["is_error"] is True
    assert "404 Not Found" in tool_result["content"]


def test_ask_stops_after_max_steps_instead_of_looping_forever():
    tool_use = ToolUseBlock(id="toolu_1", name="list_machines", input={})
    responses = [FakeResponse(content=[tool_use], stop_reason="tool_use") for _ in range(MAX_AGENT_STEPS + 2)]
    anthropic = FakeAnthropic(responses)
    agent = FactoryPulseAgent(anthropic, FakeDispatcher(result=[]), "claude-sonnet-4-6")

    answer = asyncio.run(agent.ask("Tell me everything about every machine forever"))

    assert "couldn't" in answer.lower() or "wasn't able" in answer.lower()
    assert len(anthropic.messages.requests) == MAX_AGENT_STEPS
