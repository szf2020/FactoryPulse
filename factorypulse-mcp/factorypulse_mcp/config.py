"""
Environment-driven configuration for the MCP server.

Keeping configuration in one small, pure module (no I/O besides reading env
vars) makes it trivial to test and to swap — e.g. point the same server at a
staging API by changing environment variables, never code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Loads variables from a local .env file if present (no-op in production,
# where real environment variables are injected by Docker/the host).
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for connecting to the FactoryPulse API."""

    api_base_url: str
    token: str | None
    transport: str
    host: str
    port: int


def load_settings() -> Settings:
    """Reads and normalizes settings from environment variables.

    Required:
        FACTORYPULSE_API:   Base URL of the FactoryPulse REST API,
                            e.g. "http://localhost:8000/api".
        FACTORYPULSE_TOKEN: Read-only JWT for the service account created via
                            `python manage.py create_service_token`.

    Optional:
        MCP_TRANSPORT: "stdio" (default, used by Claude Desktop / `mcp dev`),
                       "sse" or "streamable-http" (for containerized/HTTP use).
        MCP_HOST / MCP_PORT: bind address for HTTP-based transports.
    """
    return Settings(
        api_base_url=os.environ.get("FACTORYPULSE_API", "http://localhost:8000/api").rstrip("/"),
        token=os.environ.get("FACTORYPULSE_TOKEN") or None,
        transport=os.environ.get("MCP_TRANSPORT", "stdio"),
        host=os.environ.get("MCP_HOST", "0.0.0.0"),
        port=int(os.environ.get("MCP_PORT", "8000")),
    )
