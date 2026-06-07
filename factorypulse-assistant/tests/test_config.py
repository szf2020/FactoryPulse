from factorypulse_assistant.config import DEFAULT_GEMINI_MODEL, load_settings

ENV_VARS = (
    "FACTORYPULSE_API",
    "FACTORYPULSE_TOKEN",
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "CORS_ALLOW_ORIGINS",
)


def _clear_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_load_settings_falls_back_to_defaults(monkeypatch):
    _clear_env(monkeypatch)

    settings = load_settings()

    assert settings.factorypulse_api == "http://localhost:8000/api"
    assert settings.factorypulse_token is None
    assert settings.gemini_api_key is None
    assert settings.gemini_model == DEFAULT_GEMINI_MODEL
    assert settings.cors_allow_origins == ()


def test_load_settings_reads_and_normalizes_env(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("FACTORYPULSE_API", "http://api.example.com/api/")
    monkeypatch.setenv("FACTORYPULSE_TOKEN", "service-token")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSecret")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", " http://localhost:5173 , http://localhost:3000 ")

    settings = load_settings()

    assert settings.factorypulse_api == "http://api.example.com/api"  # trailing slash stripped
    assert settings.factorypulse_token == "service-token"
    assert settings.gemini_api_key == "AIzaSecret"
    assert settings.gemini_model == "gemini-2.5-pro"
    assert settings.cors_allow_origins == ("http://localhost:5173", "http://localhost:3000")


def test_load_settings_treats_blank_values_as_missing(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("FACTORYPULSE_TOKEN", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "")

    settings = load_settings()

    assert settings.factorypulse_token is None
    assert settings.gemini_api_key is None
    assert settings.gemini_model == DEFAULT_GEMINI_MODEL
    assert settings.cors_allow_origins == ()
