"""
Abstract base class that every AI provider must implement.

Architecture rule:
  The Agent NEVER imports a concrete provider directly.
  It only uses BaseProvider through the factory in ai/provider.py.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    """
    Contract that all AI providers must satisfy.

    Methods
    -------
    generate(messages, tools)
        Send a chat request and return the model's response object.
        The response must expose:
          - .content      : str | None   — final text response
          - .tool_calls   : list | None  — tool invocations requested by the model

    list_models()
        Return a list of model names available on this provider.

    health_check()
        Return True if the provider is reachable and ready.

    supports_tools()
        Return True if the current model supports OpenAI-style function/tool calling.
        When False, the agent will NOT pass tools to generate() and will operate
        in pure conversational mode.

    Properties
    ----------
    name    : Human-readable provider name (e.g. "ollama", "openrouter").
    model   : The exact model identifier being used.
    """

    # ── Abstract interface ─────────────────────────────────────────────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Exact model name/ID being used for requests."""
        ...

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
    ) -> Any:
        """
        Send a chat completion request.

        Args:
            messages : Full conversation history in OpenAI message-list format.
            tools    : Optional list of OpenAI function-calling tool schemas.
                       Pass None (or omit) when the model does not support tools.

        Returns:
            A message-like object with `.content` and `.tool_calls` attributes.
        """
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        """Return available model names on this provider."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider endpoint is reachable and operational."""
        ...

    @abstractmethod
    def supports_tools(self) -> bool:
        """
        Return True if the currently selected model supports tool/function calling.

        When False, the agent omits the tools parameter from generate() calls
        and operates in conversational mode only.
        """
        ...

    # ── Helpers ────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model!r}>"
