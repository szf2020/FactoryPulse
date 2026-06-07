"""
Exercises FactoryPulseAgent's tool-calling loop end to end against fakes for
both collaborators (the Gemini client and the tool dispatcher) — no network,
no API key and no FactoryPulse instance needed.

Fake "model responses" are built from the real `google.genai.types` objects
(Content, Part, Candidate, GenerateContentResponse) rather than hand-rolled
stand-ins, so a mismatch between our code and the SDK's actual shapes — e.g.
how function calls/results are matched and nested — surfaces here too.
"""
import asyncio

from google.genai import types

from factorypulse_assistant.agent import MAX_AGENT_STEPS, FactoryPulseAgent
from factorypulse_assistant.tools import UnknownToolError


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


def _empty_response():
    """Mimics the (real, observed) Gemini reply that carries no content parts."""
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(role="model", parts=None),
                finish_reason=types.FinishReason.STOP,
            )
        ]
    )


class FakeAsyncModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []

    async def generate_content(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


class FakeAio:
    def __init__(self, responses):
        self.models = FakeAsyncModels(responses)


class FakeGenAIClient:
    def __init__(self, responses):
        self.aio = FakeAio(responses)


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


def _agent(responses, dispatcher=None, model="gemini-2.5-flash"):
    client = FakeGenAIClient(responses)
    return client, FactoryPulseAgent(client, dispatcher or FakeDispatcher(), model)


def test_ask_returns_text_when_model_answers_without_tools():
    _, agent = _agent([_model_response(_text_part("DB-01 is running fine."))])

    answer = asyncio.run(agent.ask("How is DB-01 doing?"))

    assert answer == "DB-01 is running fine."


def test_ask_sends_question_model_and_tool_catalogue(monkeypatch):
    client, agent = _agent([_model_response(_text_part("ok"))], model="gemini-2.5-pro")

    asyncio.run(agent.ask("ping"))

    request = client.aio.models.requests[0]
    assert request["model"] == "gemini-2.5-pro"
    assert request["contents"] == [types.Content(role="user", parts=[types.Part.from_text(text="ping")])]
    [tool] = request["config"].tools
    assert {decl.name for decl in tool.function_declarations} >= {"get_oee", "list_machines"}
    assert "FactoryPulse" in request["config"].system_instruction


def test_ask_executes_requested_tool_and_returns_final_answer():
    responses = [
        _model_response(_call_part("get_oee", machine_id="DB-01", period="7d")),
        _model_response(_text_part("DB-01's OEE over 7 days is 80%.")),
    ]
    dispatcher = FakeDispatcher(result={"oee": {"global": 80.0}})
    _, agent = _agent(responses, dispatcher)

    answer = asyncio.run(agent.ask("What's DB-01's OEE this week?"))

    assert answer == "DB-01's OEE over 7 days is 80%."
    assert dispatcher.calls == [("get_oee", {"machine_id": "DB-01", "period": "7d"})]


def test_ask_feeds_tool_result_back_to_the_model():
    call_part = _call_part("get_oee", machine_id="DB-01")
    responses = [
        _model_response(call_part),
        _model_response(_text_part("done")),
    ]
    dispatcher = FakeDispatcher(result={"oee": {"global": 80.0}})
    client, agent = _agent(responses, dispatcher)

    asyncio.run(agent.ask("What's DB-01's OEE?"))

    second_request = client.aio.models.requests[1]
    assert second_request["contents"][1] == types.Content(role="model", parts=[call_part])

    feedback = second_request["contents"][2]
    assert feedback.role == "user"
    assert feedback.parts == [
        types.Part.from_function_response(
            name="get_oee", response={"result": {"oee": {"global": 80.0}}}
        )
    ]


def test_ask_reports_unknown_tool_as_a_function_error():
    call_part = _call_part("delete_machine")
    responses = [
        _model_response(call_part),
        _model_response(_text_part("I can't do that.")),
    ]
    dispatcher = FakeDispatcher(error=UnknownToolError("delete_machine"))
    client, agent = _agent(responses, dispatcher)

    asyncio.run(agent.ask("Delete DB-01"))

    [feedback_part] = client.aio.models.requests[1]["contents"][2].parts
    assert feedback_part.function_response.response == {"error": "Unknown tool: delete_machine"}


def test_ask_reports_tool_failures_as_a_function_error_instead_of_raising():
    call_part = _call_part("get_oee", machine_id="UNKNOWN")
    responses = [
        _model_response(call_part),
        _model_response(_text_part("That machine doesn't seem to exist.")),
    ]
    dispatcher = FakeDispatcher(error=RuntimeError("404 Not Found"))
    client, agent = _agent(responses, dispatcher)

    answer = asyncio.run(agent.ask("What's UNKNOWN's OEE?"))

    assert answer == "That machine doesn't seem to exist."
    [feedback_part] = client.aio.models.requests[1]["contents"][2].parts
    assert "404 Not Found" in feedback_part.function_response.response["error"]


def test_ask_returns_a_friendly_message_when_the_model_sends_back_no_parts():
    _, agent = _agent([_empty_response()])

    answer = asyncio.run(agent.ask("Qual o OEE da DB-01?"))

    assert "try asking again" in answer.lower()


def test_ask_stops_after_max_steps_instead_of_looping_forever():
    responses = [_model_response(_call_part("list_machines")) for _ in range(MAX_AGENT_STEPS + 2)]
    dispatcher = FakeDispatcher(result=[])
    client, agent = _agent(responses, dispatcher)

    answer = asyncio.run(agent.ask("Tell me everything about every machine forever"))

    assert "couldn't" in answer.lower() or "wasn't able" in answer.lower()
    assert len(client.aio.models.requests) == MAX_AGENT_STEPS
