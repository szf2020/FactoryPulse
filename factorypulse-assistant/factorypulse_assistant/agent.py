"""
Agentic loop: lets Claude answer shop-floor questions by calling FactoryPulse
analytics tools (via tool use / function calling) until it has enough
information to respond in plain text.
"""
from __future__ import annotations

import json
from typing import Any

from anthropic import AsyncAnthropic

from .tools import TOOL_DEFINITIONS, ToolDispatcher, UnknownToolError

SYSTEM_PROMPT = (
    "You are the FactoryPulse shop-floor assistant. You answer questions "
    "about machine performance, OEE (Overall Equipment Effectiveness) and "
    "downtime using the tools provided — never guess numbers. Call "
    "list_machines first if you need to resolve a machine name to its "
    "device_id. Keep answers concise and grounded in the tool results."
)

# Bounds how many tool round-trips a single question can trigger, so a
# confused model can't loop indefinitely and run up cost/latency.
MAX_AGENT_STEPS = 8


class FactoryPulseAgent:
    """Runs Claude's tool-use loop against FactoryPulse's read-only API.

    The loop: ask Claude -> if it requests tool calls, execute them through
    `ToolDispatcher` and feed the results back as `tool_result` blocks ->
    repeat until Claude replies with plain text (or the step budget runs out).
    """

    def __init__(self, anthropic: AsyncAnthropic, dispatcher: ToolDispatcher, model: str):
        self._anthropic = anthropic
        self._dispatcher = dispatcher
        self._model = model

    async def ask(self, question: str) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": question}]

        for _ in range(MAX_AGENT_STEPS):
            response = await self._anthropic.messages.create(
                model=self._model,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                return self._extract_text(response.content)

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": await self._run_tools(response.content)})

        return (
            "I wasn't able to finish answering that within the available "
            "tool-call budget — try asking about one machine or metric at a time."
        )

    async def _run_tools(self, content_blocks: list[Any]) -> list[dict[str, Any]]:
        return [
            await self._run_tool(block)
            for block in content_blocks
            if block.type == "tool_use"
        ]

    async def _run_tool(self, block: Any) -> dict[str, Any]:
        try:
            output = await self._dispatcher.dispatch(block.name, block.input)
        except UnknownToolError as exc:
            return self._tool_result(block.id, str(exc), is_error=True)
        except Exception as exc:
            # FactoryPulse API failures (bad machine id, upstream errors, ...)
            # are reported back to the model as a tool error, not a 500 — the
            # model can then explain the problem or try a different tool.
            return self._tool_result(block.id, f"Tool call failed: {exc}", is_error=True)
        return self._tool_result(block.id, json.dumps(output))

    @staticmethod
    def _tool_result(tool_use_id: str, content: str, *, is_error: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": content,
        }
        if is_error:
            result["is_error"] = True
        return result

    @staticmethod
    def _extract_text(content_blocks: list[Any]) -> str:
        return "".join(block.text for block in content_blocks if block.type == "text").strip()
