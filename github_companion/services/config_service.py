import json
import os
import threading
from pathlib import Path

GC_DIR = Path.home() / ".gc"
CONFIG_PATH = GC_DIR / "config.json"

_config_lock = threading.Lock()



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
    with _config_lock:
        if not CONFIG_PATH.exists():
            return {}
        with open(CONFIG_PATH, "r") as f:
            try:
                data = json.load(f)
                import os
                from rich import print as rprint
                debug_mode = (
                    os.environ.get("DEBUG") == "True"
                    or os.environ.get("GC_DEBUG") == "true"
                )
                if debug_mode:
                    or_detected = bool(data.get("openrouter_api_key"))
                    nv_detected = bool(data.get("nvidia_api_key"))
                    gh_detected = bool(data.get("github_token"))
                    rprint()
                    rprint("Config loaded successfully")
                    rprint(f"OpenRouter key detected: {or_detected}")
                    rprint(f"NVIDIA NIM key detected: {nv_detected}")
                    rprint(f"GitHub token detected: {gh_detected}")
                    rprint()
                return data
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
    """Return the model used for code generation tasks (default from registry)."""
    val = _load().get("coding_model")
    if not val:
        try:
            from github_companion.ai.model_registry import get_models_by_role
            recs = [m for m in get_models_by_role("coding") if m.get("recommended")]
            return recs[0]["model_id"] if recs else "qwen2.5-coder"
        except Exception:
            return "qwen2.5-coder"
    return val


def get_reasoning_model() -> str:
    """Return the model used for reasoning/planning tasks (default from registry)."""
    val = _load().get("reasoning_model")
    if not val:
        try:
            from github_companion.ai.model_registry import get_models_by_role
            recs = [m for m in get_models_by_role("planning") if m.get("recommended")]
            return recs[0]["model_id"] if recs else "deepseek-r1"
        except Exception:
            return "deepseek-r1"
    return val


def get_assistant_model() -> str:
    """Return the model used for general assistant tasks (default from registry)."""
    val = _load().get("assistant_model")
    if not val:
        try:
            from github_companion.ai.model_registry import get_models_by_role
            recs = [m for m in get_models_by_role("assistant") if m.get("recommended")]
            return recs[0]["model_id"] if recs else "llama3.3"
        except Exception:
            return "llama3.3"
    return val


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


def get_nvidia_api_key() -> str:
    """Return the NVIDIA NIM API key, or empty string if not configured."""
    key = _load().get("nvidia_api_key", "")
    if key in ("YOUR_NVIDIA_KEY_HERE", "YOUR_KEY"):
        return ""
    return key




def save_settings(settings: dict) -> None:
    """Save the settings dict back to config.json."""
    with _config_lock:
        ensure_gc_directories()
        with open(CONFIG_PATH, "w") as f:
            json.dump(settings, f, indent=4)

    import os
    from rich import print as rprint
    debug_mode = (
        os.environ.get("DEBUG") == "True"
        or os.environ.get("GC_DEBUG") == "true"
    )
    if debug_mode:
        keys = list(settings.keys())
        or_val = settings.get("openrouter_api_key", "")
        or_len = len(or_val) if or_val else 0
        nv_val = settings.get("nvidia_api_key", "")
        nv_len = len(nv_val) if nv_val else 0
        rprint()
        rprint("✓ Config saved")
        rprint(f"Path: {CONFIG_PATH}")
        rprint(f"Stored keys: {keys}")
        rprint(f"OpenRouter key length: {or_len}")
        rprint(f"NVIDIA NIM key length: {nv_len}")
        rprint()


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


def get_default_workspace() -> str:
    """Return the default workspace directory, or empty string if not set."""
    return _load().get("workspace", "")


def run_startup_diagnostics() -> None:
    """Print configuration diagnostics if GC_DEBUG or DEBUG env variable is set."""
    import os
    from rich import print as rprint
    debug_mode = (
        os.environ.get("DEBUG") == "True"
        or os.environ.get("GC_DEBUG") == "true"
    )
    if not debug_mode:
        return

    exists = CONFIG_PATH.exists()
    keys = []
    or_exists = False
    or_len = 0
    nv_exists = False
    nv_len = 0
    mtime_str = "N/A"
    
    if exists:
        try:
            # Bypass load diagnostics trigger by loading directly
            with open(CONFIG_PATH, "r") as f:
                settings = json.load(f)
            keys = list(settings.keys())
            or_val = settings.get("openrouter_api_key", "")
            or_exists = bool(or_val)
            or_len = len(or_val) if or_val else 0
            
            nv_val = settings.get("nvidia_api_key", "")
            nv_exists = bool(nv_val)
            nv_len = len(nv_val) if nv_val else 0
            
            mtime = os.path.getmtime(CONFIG_PATH)
            import datetime
            mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass

    rprint()
    rprint("====================================================")
    rprint("Configuration Startup Diagnostics")
    rprint(f"Config path: {CONFIG_PATH}")
    rprint(f"Config exists: {exists}")
    rprint(f"Keys present: {keys}")
    rprint(f"OpenRouter key exists: {or_exists}")
    rprint(f"OpenRouter key length: {or_len}")
    rprint(f"NVIDIA NIM key exists: {nv_exists}")
    rprint(f"NVIDIA NIM key length: {nv_len}")
    rprint(f"Last modified time of config.json: {mtime_str}")
    rprint("====================================================")
    rprint()