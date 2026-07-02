"""
NVIDIA NIM provider — stub for future implementation.

NVIDIA NIM provides high-performance, optimized inference for open models
including DeepSeek, Qwen, Llama Nemotron, and Mistral.

Status: NOT YET IMPLEMENTED
        Set provider="nvidia" in settings.json to get a clear error
        prompting you to wait for this provider to be implemented.
"""
from __future__ import annotations
from typing import Any

from ai.providers.base_provider import BaseProvider


class NvidiaProvider(BaseProvider):
    """
    Placeholder for NVIDIA NIM inference provider.

    All methods raise NotImplementedError until the provider is implemented.
    health_check() returns False so the factory falls back to OpenRouter.
    """

    @property
    def name(self) -> str:
        return "nvidia"

    @property
    def model(self) -> str:
        return "not-implemented"

    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        raise NotImplementedError(
            "NVIDIA NIM provider is not yet implemented.\n"
            "  Use provider='ollama' or provider='openrouter' in config/settings.json"
        )

    def list_models(self) -> list[str]:
        return []

    def health_check(self) -> bool:
        # Always returns False so the factory automatically falls back
        return False

    def supports_tools(self) -> bool:
        return False
