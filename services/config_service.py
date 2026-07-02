import json

CONFIG_PATH = "config/settings.json"


def _load() -> dict:
    """Load settings.json once and return the dict."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def get_github_username() -> str:
    return _load()["github_username"]


def get_github_token() -> str:
    return _load()["github_token"]


def get_openai_api_key() -> str:
    """Return the OpenAI API key from settings, raising a clear error if missing."""
    key = _load().get("openai_api_key", "")
    if not key or key == "YOUR_OPENAI_KEY_HERE":
        raise ValueError(
            "OpenAI API key not configured.\n"
            "  Open config/settings.json and add:\n"
            '  "openai_api_key": "sk-..."'
        )
    return key


def get_ai_model() -> str:
    """Return the configured AI model, defaulting to gpt-4o-mini."""
    return _load().get("ai_model", "gpt-4o-mini")