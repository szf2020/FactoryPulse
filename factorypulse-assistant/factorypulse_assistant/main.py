"""
FastAPI app exposing FactoryPulse's agentic assistant over HTTP.

    POST /ask {"question": "What's DB-01's OEE this week?"}
    -> {"answer": "DB-01's global OEE over the last 7 days is ..."}

Local development:
    uvicorn factorypulse_assistant.main:app --reload
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from anthropic import AsyncAnthropic
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from factorypulse_mcp.client import FactoryPulseClient

from .agent import FactoryPulseAgent
from .config import load_settings
from .tools import ToolDispatcher

settings = load_settings()
factorypulse_client = FactoryPulseClient(settings.factorypulse_api, settings.factorypulse_token)
agent = FactoryPulseAgent(
    anthropic=AsyncAnthropic(api_key=settings.anthropic_api_key),
    dispatcher=ToolDispatcher(factorypulse_client),
    model=settings.anthropic_model,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await factorypulse_client.aclose()


app = FastAPI(title="FactoryPulse Assistant", lifespan=lifespan)

if settings.cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_methods=["POST"],
        allow_headers=["*"],
    )


class AskRequest(BaseModel):
    question: str = Field(min_length=1, description="A natural-language question about the shop floor.")


class AskResponse(BaseModel):
    answer: str


def get_agent() -> FactoryPulseAgent:
    """FastAPI dependency — overridden with a fake in tests (see test_main.py)."""
    return agent


@app.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, agent: FactoryPulseAgent = Depends(get_agent)) -> AskResponse:
    return AskResponse(answer=await agent.ask(payload.question))
