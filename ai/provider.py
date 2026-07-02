"""OpenAI communication layer for the GitHub Companion AI agent."""
from __future__ import annotations
from typing import Any

try:
    import openai
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


class OpenAIProvider:
    """
    Thin wrapper around openai.chat.completions.create with tool-calling support.

    Returns the raw `message` object from the first choice so the agent can
    inspect `.content` and `.tool_calls` directly.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not _OPENAI_AVAILABLE:
            raise RuntimeError(
                "The 'openai' package is not installed.\n"
                "  Run:  pip install openai"
            )
        self.model  = model
        self.client = openai.OpenAI(api_key=api_key)

    def chat(self, messages: list[dict[str, Any]], tools: list[dict]) -> Any:
        """
        Send a chat request to OpenAI with the given messages and tool schemas.

        Args:
            messages : Full conversation history in OpenAI message-list format.
            tools    : List of OpenAI function-calling tool schemas.

        Returns:
            The `message` object (choice[0].message) from the API response.
            Callers should check:
              - response.tool_calls  — if not None, the model wants to call tools.
              - response.content     — the final text response when no tool calls remain.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.2,      # Low temp for consistent, predictable tool use
            max_tokens=2048,
        )
        return response.choices[0].message
