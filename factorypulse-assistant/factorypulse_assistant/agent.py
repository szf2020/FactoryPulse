"""
Agentic loop: lets Gemini answer shop-floor questions by calling FactoryPulse
analytics tools (via function calling) until it has enough information to
respond in plain text.
"""
from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from .tools import TOOL_DEFINITIONS, ToolDispatcher, UnknownToolError

SYSTEM_PROMPT = (
    "You are the FactoryPulse shop-floor assistant. You answer questions "
    "about machine performance, OEE (Overall Equipment Effectiveness) and "
    "downtime using the tools provided — never guess numbers. Call "
    "list_machines first if you need to resolve a machine name to its "
    "device_id, but always call get_oee for the actual OEE figures — "
    "list_machines' OEE field is just a cached snapshot that is frequently "
    "null, and reporting it (or its absence) as the answer would be wrong. "
    "Keep answers concise and grounded in the tool results. The chat UI "
    "displays your reply as plain text, not rendered Markdown — so write in "
    "plain prose and never use Markdown syntax (no '*', '**', '#', '-' "
    "bullets or code fences); use line breaks and short sentences instead "
    "of lists or bold text to structure multi-machine answers."
)

# Bounds how many tool round-trips a single question can trigger, so a
# confused model can't loop indefinitely and run up cost/latency.
MAX_AGENT_STEPS = 8


class FactoryPulseAgent:
    """Runs Gemini's function-calling loop against FactoryPulse's read-only API.

    The loop: ask Gemini -> if it requests function calls, execute them
    through `ToolDispatcher` and feed the results back as `function_response`
    parts -> repeat until Gemini replies in plain text (or the step budget
    runs out).
    """

    def __init__(self, client: genai.Client, dispatcher: ToolDispatcher, model: str):
        self._client = client
        self._dispatcher = dispatcher
        self._model = model
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=TOOL_DEFINITIONS)],
        )

    async def ask(self, question: str) -> str:
        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=question)])
        ]

        for _ in range(MAX_AGENT_STEPS):
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=self._config,
            )

            content = response.candidates[0].content
            parts = content.parts if content is not None else None
            if not parts:
                # Observed in practice with gemini-2.5-flash-lite: an empty
                # reply (content or its parts is None) with finish_reason
                # STOP — nothing to act on or report, so don't crash the
                # request, just ask the user to retry.
                return (
                    "The model didn't return a usable reply for that "
                    "question — please try asking again in a moment."
                )

            calls = [part.function_call for part in parts if part.function_call]
            if not calls:
                return self._extract_text(parts)

            contents.append(content)
            contents.append(types.Content(role="user", parts=await self._run_tools(calls)))

        return (
            "I wasn't able to finish answering that within the available "
            "tool-call budget — try asking about one machine or metric at a time."
        )

    async def _run_tools(self, calls: list[Any]) -> list[types.Part]:
        return [await self._run_tool(call) for call in calls]

    async def _run_tool(self, call: Any) -> types.Part:
        try:
            output = await self._dispatcher.dispatch(call.name, dict(call.args or {}))
        except UnknownToolError as exc:
            return self._tool_error(call.name, str(exc))
        except Exception as exc:
            # FactoryPulse API failures (bad machine id, upstream errors, ...)
            # are reported back to the model as a function error, not a 500 —
            # the model can then explain the problem or try a different tool.
            return self._tool_error(call.name, f"Tool call failed: {exc}")
        return types.Part.from_function_response(name=call.name, response={"result": output})

    @staticmethod
    def _tool_error(name: str, message: str) -> types.Part:
        return types.Part.from_function_response(name=name, response={"error": message})

    @staticmethod
    def _extract_text(parts: list[Any]) -> str:
        return "".join(part.text for part in parts if part.text).strip()
