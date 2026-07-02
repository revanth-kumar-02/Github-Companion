"""
Provider factory for the GitHub Companion AI agent.

This module is the ONLY place that knows about concrete provider classes.
The Agent imports get_provider() from here and receives a BaseProvider
— it never imports OllamaProvider, OpenRouterProvider, etc. directly.

Fallback strategy
-----------------
1. Try the configured primary provider (default: ollama).
2. If its health_check() fails, warn the user and try the fallback provider.
3. If both fail, raise a RuntimeError with clear setup instructions.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai.providers.base_provider import BaseProvider

from rich import print as rprint

from services.config_service import (
    get_ai_provider,
    get_coding_model,
    get_reasoning_model,
    get_assistant_model,
    get_fallback_provider,
    get_openrouter_api_key,
    get_ollama_host,
)


# ── Public API ─────────────────────────────────────────────────────────────────

def get_provider(model_type: str = "assistant") -> "BaseProvider":
    """
    Return a ready-to-use provider for the given model type.

    Args:
        model_type : "coding" | "reasoning" | "assistant"

    Returns:
        A concrete BaseProvider instance (Ollama, OpenRouter, etc.)

    Raises:
        RuntimeError if no provider is reachable.
    """
    primary_name  = get_ai_provider()
    fallback_name = get_fallback_provider()
    model_name    = _resolve_model_name(model_type)

    # ── Try primary ────────────────────────────────────────────────────────────
    primary = _build_provider(primary_name, model_name)
    if primary is not None and primary.health_check():
        return primary

    # ── Primary unreachable — try fallback ─────────────────────────────────────
    if fallback_name and fallback_name != primary_name:
        rprint(
            f"[bold yellow]  ⚠  {primary_name.capitalize()} is unavailable. "
            f"Switching to {fallback_name}...[/bold yellow]"
        )
        fallback = _build_provider(fallback_name, model_name)
        if fallback is not None and fallback.health_check():
            return fallback

    # ── Both failed ────────────────────────────────────────────────────────────
    _raise_no_provider(primary_name, fallback_name)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _resolve_model_name(model_type: str) -> str:
    """Map model type string to the configured model name."""
    mapping = {
        "coding":    get_coding_model,
        "reasoning": get_reasoning_model,
        "assistant": get_assistant_model,
    }
    return mapping.get(model_type, get_assistant_model)()


def _build_provider(provider_name: str, model_name: str) -> "BaseProvider | None":
    """
    Instantiate a concrete provider.

    Returns None (rather than raising) so the factory can silently try fallback.
    """
    try:
        # Check custom models first
        from services.config_service import get_custom_models
        for custom_cfg in get_custom_models():
            if custom_cfg.get("model_name") == model_name or custom_cfg.get("provider_name") == provider_name:
                from ai.providers.custom_provider import CustomProvider
                return CustomProvider(custom_cfg)

        if provider_name == "ollama":
            from ai.providers.ollama_provider import OllamaProvider
            return OllamaProvider(model_name=model_name, host=get_ollama_host())

        if provider_name == "openrouter":
            from ai.providers.openrouter_provider import OpenRouterProvider
            key = get_openrouter_api_key()
            return OpenRouterProvider(model_name=model_name, api_key=key)

        if provider_name == "nvidia":
            from ai.providers.nvidia_provider import NvidiaProvider
            return NvidiaProvider()

        rprint(f"[red]  Unknown provider: '{provider_name}'[/red]")
        return None

    except Exception:
        # Swallow all errors during construction so fallback can be tried
        return None



def _raise_no_provider(primary: str, fallback: str) -> None:
    """Raise a clear, actionable error when no provider is reachable."""
    msg_parts = [
        "No AI provider is available.",
        "",
        f"  Primary  ({primary})  : unreachable or not configured",
        f"  Fallback ({fallback}) : unreachable or not configured",
        "",
    ]
    if primary == "ollama" or fallback == "ollama":
        msg_parts.append("  To start Ollama:  ollama serve")
        msg_parts.append("  To pull a model:  ollama pull qwen2.5-coder")
    if primary == "openrouter" or fallback == "openrouter":
        msg_parts.append("  For OpenRouter:   add 'openrouter_api_key' to config/settings.json")
        msg_parts.append("  Get a free key:   https://openrouter.ai/keys")

    raise RuntimeError("\n".join(msg_parts))
