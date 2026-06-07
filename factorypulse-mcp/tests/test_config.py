from factorypulse_mcp.config import load_settings

ENV_VARS = ("FACTORYPULSE_API", "FACTORYPULSE_TOKEN", "MCP_TRANSPORT", "MCP_HOST", "MCP_PORT")


def _clear_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_load_settings_falls_back_to_defaults(monkeypatch):
    _clear_env(monkeypatch)

    settings = load_settings()

    assert settings.api_base_url == "http://localhost:8000/api"
    assert settings.token is None
    assert settings.transport == "stdio"
    assert settings.port == 8000


def test_load_settings_reads_env_and_normalizes_values(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("FACTORYPULSE_API", "http://api.example.com/api/")
    monkeypatch.setenv("FACTORYPULSE_TOKEN", "secret-token")
    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("MCP_PORT", "9100")

    settings = load_settings()

    assert settings.api_base_url == "http://api.example.com/api"  # trailing slash stripped
    assert settings.token == "secret-token"
    assert settings.transport == "streamable-http"
    assert settings.port == 9100


def test_load_settings_treats_empty_token_as_missing(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("FACTORYPULSE_TOKEN", "")

    assert load_settings().token is None
