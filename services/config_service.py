import json

CONFIG_PATH = "config/settings.json"


def _load() -> dict:
    """Load settings.json and return the dict."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


# ── GitHub ─────────────────────────────────────────────────────────────────────

def get_github_username() -> str:
    return _load()["github_username"]


def get_github_token() -> str:
    return _load()["github_token"]


# ── AI Provider ────────────────────────────────────────────────────────────────

def get_ai_provider() -> str:
    """Return the primary AI provider name (default: 'ollama')."""
    return _load().get("provider", "ollama")


def get_fallback_provider() -> str:
    """Return the fallback AI provider name (default: 'openrouter')."""
    return _load().get("fallback_provider", "openrouter")


# ── AI Models ──────────────────────────────────────────────────────────────────

def get_coding_model() -> str:
    """Return the model used for code generation tasks (default: 'qwen2.5-coder')."""
    return _load().get("coding_model", "qwen2.5-coder")


def get_reasoning_model() -> str:
    """Return the model used for reasoning/planning tasks (default: 'deepseek-r1')."""
    return _load().get("reasoning_model", "deepseek-r1")


def get_assistant_model() -> str:
    """Return the model used for general assistant tasks (default: 'llama3.3')."""
    return _load().get("assistant_model", "llama3.3")


# ── Provider-specific config ───────────────────────────────────────────────────

def get_ollama_host() -> str:
    """Return the Ollama host URL (default: 'http://localhost:11434')."""
    return _load().get("ollama_host", "http://localhost:11434")


def get_openrouter_api_key() -> str:
    """
    Return the OpenRouter API key.

    Raises:
        ValueError if the key is missing or still set to the placeholder.
    """
    key = _load().get("openrouter_api_key", "")
    if not key or key in ("YOUR_OPENROUTER_KEY_HERE", "YOUR_KEY"):
        raise ValueError(
            "OpenRouter API key not configured.\n"
            "  Open config/settings.json and set:\n"
            '  "openrouter_api_key": "sk-or-..."'
        )
    return key