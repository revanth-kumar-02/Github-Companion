"""In-memory conversation history for the GitHub Companion AI agent."""
from __future__ import annotations
from typing import Any


class ConversationMemory:
    """
    Stores the full conversation in OpenAI message-list format.

    Each message is a dict with 'role' and 'content' (plus optional
    'tool_calls' / 'tool_call_id' for the function-calling protocol).
    """

    def __init__(self, max_history: int = 40):
        self._messages: list[dict[str, Any]] = []
        self.max_history = max_history

    # ── Write ──────────────────────────────────────────────────────────────

    def add_user(self, content: str) -> None:
        self._messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant(self, content: str | None, tool_calls: list | None = None) -> None:
        msg: dict[str, Any] = {"role": "assistant", "content": content or ""}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self._messages.append(msg)
        self._trim()

    def add_tool_result(self, tool_call_id: str, content: str) -> None:
        self._messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        })

    # ── Read ───────────────────────────────────────────────────────────────

    def get_history(self) -> list[dict[str, Any]]:
        """Return a shallow copy of the message list."""
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)

    # ── Internal ───────────────────────────────────────────────────────────

    def _trim(self) -> None:
        """Keep only the most recent messages to avoid token overflow."""
        if len(self._messages) > self.max_history:
            self._messages = self._messages[-self.max_history:]
