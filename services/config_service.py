import json
import os
from pathlib import Path

GC_DIR = Path.home() / ".gc"
CONFIG_PATH = GC_DIR / "config.json"


def is_configured() -> bool:
    """Check if the configuration file exists."""
    return CONFIG_PATH.exists()


def ensure_gc_directories() -> None:
    """Ensure all required .gc directories exist."""
    GC_DIR.mkdir(parents=True, exist_ok=True)
    (GC_DIR / "cache").mkdir(parents=True, exist_ok=True)
    (GC_DIR / "logs").mkdir(parents=True, exist_ok=True)
    (GC_DIR / "sessions").mkdir(parents=True, exist_ok=True)
    history_file = GC_DIR / "history.json"
    if not history_file.exists():
        with open(history_file, "w") as f:
            json.dump([], f)


def _load() -> dict:
    """Load config.json and return the dict."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


# ── GitHub ─────────────────────────────────────────────────────────────────────

def get_github_username() -> str:
    return _load().get("github_username", "")


def get_github_token() -> str:
    return _load().get("github_token", "")


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
    """Return the OpenRouter API key, or empty string if not configured."""
    key = _load().get("openrouter_api_key", "")
    if key in ("YOUR_OPENROUTER_KEY_HERE", "YOUR_KEY"):
        return ""
    return key



def save_settings(settings: dict) -> None:
    """Save the settings dict back to config.json."""
    ensure_gc_directories()
    with open(CONFIG_PATH, "w") as f:
        json.dump(settings, f, indent=4)


def get_custom_models() -> list[dict]:
    """Return the list of custom registered models."""
    return _load().get("custom_models", [])


def add_custom_model(model: dict) -> None:
    """Register a new custom model in the settings config."""
    settings = _load()
    if "custom_models" not in settings:
        settings["custom_models"] = []
    settings["custom_models"].append(model)
    save_settings(settings)