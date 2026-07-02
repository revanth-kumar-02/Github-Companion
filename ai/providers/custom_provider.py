"""Custom provider for user-registered OpenAI-compatible API endpoints."""
from __future__ import annotations
from typing import Any
from ai.providers.base_provider import BaseProvider


class CustomProvider(BaseProvider):
    """
    Connects to an arbitrary user-registered OpenAI-compatible API.
    """

    def __init__(self, config: dict):
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")

        self.config = config
        self._name = config.get("provider_name", "custom")
        self._model = config.get("model_name", "custom-model")
        self._endpoint = config.get("api_endpoint", "").rstrip("/")
        self._api_key = config.get("api_key", "")
        self._headers = config.get("headers", {})
        self._temperature = float(config.get("temperature", 0.2))
        self._max_tokens = int(config.get("max_tokens", 2048))
        self._client = OpenAI(
            base_url=self._endpoint,
            api_key=self._api_key,
            default_headers=self._headers,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if tools and self.supports_tools():
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        return response.choices[0].message

    def list_models(self) -> list[str]:
        return [self._model]

    def health_check(self) -> bool:
        # Check that the endpoint and key are configured
        return bool(self._endpoint and self._api_key)

    def supports_tools(self) -> bool:
        # Assume custom coding models support tools unless they are deepseek-r1
        model_lower = self._model.lower()
        if "r1" in model_lower:
            return False
        return True
