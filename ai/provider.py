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
    
    from ai.model_registry import get_models_by_provider, get_model_by_display_name_or_id
    
    # Resolve the model name using the requested model_type (role)
    model_name    = _resolve_model_name(model_type)

    if primary_name.lower() == "auto":
        priority = ["ollama", "nvidia", "openrouter"]
        for prov_name in priority:
            # Dynamically look up the model for the provider and the required role
            role_key = "planning" if model_type == "reasoning" else model_type
            prov_models = get_models_by_provider(prov_name)
            
            # Find the match for this role, preferring recommended ones
            matching_model = None
            for m in prov_models:
                if m["role"].lower() == role_key.lower():
                    if m.get("recommended"):
                        matching_model = m
                        break
                    if matching_model is None:
                        matching_model = m
            
            if matching_model:
                prov = _build_provider(prov_name, matching_model["model_id"])
                if prov is not None and prov.health_check():
                    rprint(f"[bold green]  ✔  Auto Selected Provider: {prov_name.upper()} ({prov.model})[/bold green]")
                    return prov
        _raise_no_provider("auto (Ollama -> NVIDIA NIM -> OpenRouter)", fallback_name)

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
    configured_val = mapping.get(model_type, get_assistant_model)()
    
    # Fallback to role-based recommended model if not configured
    from ai.model_registry import get_models_by_role
    reg_model = get_model_by_display_name_or_id(configured_val)
    if reg_model:
        return reg_model["model_id"]
        
    role_key = "planning" if model_type == "reasoning" else model_type
    role_models = get_models_by_role(role_key)
    for m in role_models:
        if m.get("recommended"):
            return m["model_id"]
            
    if role_models:
        return role_models[0]["model_id"]
        
    return configured_val


def _build_provider(provider_name: str, model_name: str) -> "BaseProvider | None":
    """
    Instantiate a concrete provider.

    Returns None (rather than raising) so the factory can silently try fallback.
    """
    try:
        # Resolve via registry if possible
        from ai.model_registry import get_model_by_display_name_or_id
        reg_model = get_model_by_display_name_or_id(model_name)
        resolved_model_id = reg_model["model_id"] if reg_model else model_name

        # Check custom models first
        from services.config_service import get_custom_models
        for custom_cfg in get_custom_models():
            if custom_cfg.get("model_name") == model_name or custom_cfg.get("provider_name") == provider_name:
                from ai.providers.custom_provider import CustomProvider
                return CustomProvider(custom_cfg)

        if provider_name == "ollama":
            from ai.providers.ollama_provider import OllamaProvider
            return OllamaProvider(model_name=resolved_model_id, host=get_ollama_host())

        if provider_name == "openrouter":
            from ai.providers.openrouter_provider import OpenRouterProvider
            key = get_openrouter_api_key()
            return OpenRouterProvider(model_name=resolved_model_id, api_key=key)

        if provider_name == "nvidia":
            from ai.providers.nvidia_provider import NvidiaProvider
            from services.config_service import get_nvidia_api_key
            key = get_nvidia_api_key()
            return NvidiaProvider(model_name=resolved_model_id, api_key=key)

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
