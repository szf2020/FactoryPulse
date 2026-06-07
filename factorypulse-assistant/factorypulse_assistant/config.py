"""
Environment-driven configuration for the assistant service.

Mirrors the approach used in `factorypulse_mcp.config`: a single pure module
(no I/O besides reading env vars and an optional `.env` file) so settings stay
trivial to test and to change per-environment without touching code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# Loads variables from a local .env file if present (no-op in production,
# where real environment variables are injected by Docker/the host).
load_dotenv()

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the assistant service."""

    factorypulse_api: str
    factorypulse_token: str | None
    gemini_api_key: str | None
    gemini_model: str
    cors_allow_origins: tuple[str, ...] = field(default_factory=tuple)


def _parse_origins(raw: str) -> tuple[str, ...]:
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


def load_settings() -> Settings:
    """Reads and normalizes settings from environment variables.

    Required:
        GEMINI_API_KEY:     API key used to call the Gemini API.
        FACTORYPULSE_TOKEN: Read-only JWT for the service account created via
                            `python manage.py create_service_token`.

    Optional:
        FACTORYPULSE_API:    Base URL of the FactoryPulse REST API
                             (default "http://localhost:8000/api").
        GEMINI_MODEL:        Gemini model id used for tool-calling
                             (default "gemini-2.5-flash").
        CORS_ALLOW_ORIGINS:  Comma-separated list of origins allowed to call
                             this service from a browser, e.g. the React
                             frontend's dev server URL. Empty by default.
    """
    return Settings(
        factorypulse_api=os.environ.get("FACTORYPULSE_API", "http://localhost:8000/api").rstrip("/"),
        factorypulse_token=os.environ.get("FACTORYPULSE_TOKEN") or None,
        gemini_api_key=os.environ.get("GEMINI_API_KEY") or None,
        gemini_model=os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL,
        cors_allow_origins=_parse_origins(os.environ.get("CORS_ALLOW_ORIGINS", "")),
    )
