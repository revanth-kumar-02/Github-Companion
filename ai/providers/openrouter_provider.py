"""
OpenRouter provider — cloud inference with access to many open models via one API key.

OpenRouter exposes an OpenAI-compatible API at https://openrouter.ai/api/v1,
so we use the standard `openai` SDK pointed at a different base_url.

Get a free API key at: https://openrouter.ai/keys
Add it to config/settings.json under "openrouter_api_key".

Supported models include DeepSeek, Qwen, Llama, Mistral and many others.
"""
from __future__ import annotations
from typing import Any

from ai.providers.base_provider import BaseProvider


# Mapping from logical model names (used in settings.json) to OpenRouter model IDs.
# Users configure short names; this map handles the provider-specific format.
_MODEL_MAP: dict[str, str] = {
    # Coding models
    "qwen2.5-coder":      "qwen/qwen2.5-coder-32b-instruct",
    "codellama":          "meta-llama/codellama-70b-instruct",
    # Reasoning models
    "deepseek-r1":        "deepseek/deepseek-r1",
    # Assistant / general models
    "deepseek-v3":        "deepseek/deepseek-chat-v3-0324",
    "llama3.3":           "meta-llama/llama-3.3-70b-instruct",
    "llama3.1":           "meta-llama/llama-3.1-70b-instruct",
    "mistral":            "mistralai/mistral-7b-instruct",
    "mixtral":            "mistralai/mixtral-8x7b-instruct",
    "qwen":               "qwen/qwen-72b-chat",
}

# Models that do NOT reliably support tool/function calling on OpenRouter.
_NO_TOOLS_MODELS: tuple[str, ...] = (
    "deepseek/deepseek-r1",  # Chain-of-thought model; tool calling not reliable
)


class OpenRouterProvider(BaseProvider):
    """
    Connects to OpenRouter's cloud inference API.

    Base URL  : https://openrouter.ai/api/v1
    Auth      : Bearer <openrouter_api_key>
    Protocol  : OpenAI-compatible chat completions
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, model_name: str, api_key: str):
        try:
            from openai import OpenAI as _OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        # Resolve logical name → OpenRouter model ID (fall through if already an ID)
        self._logical_model = model_name
        self._model         = _MODEL_MAP.get(model_name, model_name)
        self._api_key       = api_key
        self._client        = _OpenAI(base_url=self.BASE_URL, api_key=api_key)

    # ── BaseProvider interface ─────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """Send a chat completion request to OpenRouter."""
        kwargs: dict[str, Any] = {
            "model":       self._model,
            "messages":    messages,
            "temperature": 0.2,
            "max_tokens":  2048,
            # OpenRouter-specific headers for identification
            "extra_headers": {
                "HTTP-Referer": "https://github.com/revanth-kumar-02/Github-Companion",
                "X-Title":      "GitHub Companion",
            },
        }
        if tools and self.supports_tools():
            kwargs["tools"]       = tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def list_models(self) -> list[str]:
        """Return the logical model names available via OpenRouter."""
        return list(_MODEL_MAP.keys())

    def health_check(self) -> bool:
        """Return True if a valid (non-placeholder) API key is configured."""
        return bool(
            self._api_key
            and self._api_key not in ("YOUR_OPENROUTER_KEY_HERE", "", "YOUR_KEY")
        )

    def supports_tools(self) -> bool:
        """Return True if the selected model reliably supports tool calling."""
        return not any(self._model.startswith(m) for m in _NO_TOOLS_MODELS)
