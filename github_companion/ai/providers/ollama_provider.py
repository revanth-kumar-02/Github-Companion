"""
Ollama provider — runs AI models locally via Ollama's OpenAI-compatible API.

Ollama exposes an OpenAI-compatible REST server at localhost:11434/v1,
so we can use the standard `openai` SDK by simply pointing it at a different base_url.

No API key is required. Models must be pulled locally first:
    ollama pull qwen2.5-coder
    ollama pull deepseek-r1
    ollama pull llama3.3
"""
from __future__ import annotations
from typing import Any

import requests as _requests

from github_companion.ai.providers.base_provider import BaseProvider


# Models confirmed to support OpenAI-style tool/function calling via Ollama.
# deepseek-r1 uses a chain-of-thought format and does NOT support tool calling.
_TOOL_CAPABLE_PREFIXES: tuple[str, ...] = (
    "qwen2.5-coder",
    "qwen2.5",
    "llama3.3",
    "llama3.1",
    "llama3.2",
    "codellama",
    "mistral",
    "mixtral",
    "command-r",
)


class OllamaProvider(BaseProvider):
    """
    Connects to a locally running Ollama instance via its OpenAI-compatible API.

    Ollama endpoint: http://localhost:11434/v1  (configurable via ollama_host)
    Auth            : api_key="ollama"  (Ollama ignores the key, just needs a non-empty value)
    """

    def __init__(self, model_name: str, host: str = "http://localhost:11434"):
        try:
            from openai import OpenAI as _OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        self._model    = model_name
        self._host     = host.rstrip("/")
        self._client   = _OpenAI(base_url=f"{self._host}/v1", api_key="ollama")

    # ── BaseProvider interface ─────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """
        Send a chat completion request to Ollama.

        Tools are only forwarded if the model supports them (supports_tools() is True).
        """
        kwargs: dict[str, Any] = {
            "model":       self._model,
            "messages":    messages,
            "temperature": 0.2,
            "max_tokens":  2048,
        }
        if tools and self.supports_tools():
            kwargs["tools"]       = tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def list_models(self) -> list[str]:
        """Return names of all models currently pulled in Ollama."""
        try:
            resp = _requests.get(f"{self._host}/api/tags", timeout=5)
            if resp.status_code == 200:
                return [m["name"] for m in resp.json().get("models", [])]
        except Exception:
            pass
        return []

    def health_check(self) -> bool:
        """Return True if Ollama is running and reachable."""
        try:
            resp = _requests.get(f"{self._host}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def supports_tools(self) -> bool:
        """
        Return True if this model supports OpenAI-style tool calling.

        Strips the tag suffix (e.g., 'qwen2.5-coder:7b' → 'qwen2.5-coder')
        before checking against the known-capable prefix list.
        """
        base_name = self._model.split(":")[0].lower()
        return any(base_name.startswith(prefix) for prefix in _TOOL_CAPABLE_PREFIXES)
