"""Design Provider Registry for GitHub Companion.

Google Stitch is the primary design provider.
If Stitch is unavailable or not configured, the registry automatically
falls back to the Internal AI Designer — no menu, no interruption.
"""
from __future__ import annotations
from rich.console import Console
from rich import print as rprint

from github_companion.design.base_designer import BaseDesigner

console = Console()


# ── Provider catalogue ─────────────────────────────────────────────────────────

def get_available_providers() -> list[dict]:
    """
    Return metadata for all registered design providers.

    Each entry contains:
        id          : str  — machine-readable identifier
        name        : str  — display name shown in the CLI menu
        description : str  — one-line description
        configured  : bool — whether credentials/config are present
        recommended : bool — whether to show ⭐ recommended badge
    """
    from github_companion.services.config_service import (
        get_stitch_api_key,
        get_stitch_mcp_server,
    )
    stitch_key = get_stitch_api_key()
    stitch_mcp = get_stitch_mcp_server()
    stitch_configured = bool(stitch_key or stitch_mcp)

    return [
        {
            "id": "internal",
            "name": "Internal AI Designer",
            "description": "LLM-powered design analysis using your active AI model",
            "configured": True,
            "recommended": not stitch_configured,
        },
        {
            "id": "stitch",
            "name": "Google Stitch",
            "description": "Google Stitch design service — professional UI generation",
            "configured": stitch_configured,
            "recommended": stitch_configured,
        },
    ]


# ── Provider factory ───────────────────────────────────────────────────────────

def get_provider(provider_id: str, ai_provider=None) -> BaseDesigner | None:
    """
    Instantiate and return the requested design provider.

    Args:
        provider_id : 'internal' or 'stitch'
        ai_provider : Active BaseProvider instance (required for 'internal')

    Returns:
        A BaseDesigner instance, or None if the id is unrecognised.
    """
    from github_companion.services.config_service import (
        get_stitch_api_key,
        get_stitch_mcp_server,
    )

    if provider_id == "internal":
        from github_companion.design.internal_designer import InternalDesigner
        return InternalDesigner(ai_provider)

    if provider_id == "stitch":
        from github_companion.design.stitch_provider import StitchProvider
        return StitchProvider(
            api_key=get_stitch_api_key(),
            mcp_server=get_stitch_mcp_server(),
        )

    return None


# ── Primary auto-resolution (no menu) ────────────────────────────────────────

def get_active_designer(ai_provider) -> BaseDesigner:
    """
    Resolve and return the active Design Provider automatically.

    Resolution order:
        1. Google Stitch  — if api_key or mcp_server is configured AND health_check() passes
        2. Internal AI Designer — silent fallback, always available

    No menu is shown. Google Stitch is the primary provider. If Stitch is
    unavailable or not yet configured, the session continues seamlessly with
    the Internal AI Designer.

    Args:
        ai_provider: The active AI BaseProvider instance (used by InternalDesigner).

    Returns:
        A ready-to-use BaseDesigner instance (never None).
    """
    from github_companion.design.internal_designer import InternalDesigner
    from github_companion.services.config_service import (
        get_stitch_api_key,
        get_stitch_mcp_server,
    )

    stitch_key = get_stitch_api_key()
    stitch_mcp = get_stitch_mcp_server()

    # Try Stitch only if credentials are present
    if stitch_key or stitch_mcp:
        from github_companion.design.stitch_provider import StitchProvider
        stitch = StitchProvider(api_key=stitch_key, mcp_server=stitch_mcp)

        with console.status("[bold yellow]Connecting to Google Stitch...[/bold yellow]", spinner="dots"):
            available = stitch.health_check()

        if available:
            rprint("[bold green]✓  Google Stitch connected.[/bold green]")
            rprint()
            return stitch

        # Stitch configured but unreachable — notify and fall back
        rprint("[bold yellow]⚠  Google Stitch unavailable. Switching to Internal Designer.[/bold yellow]")
        rprint()

    # Default: Internal AI Designer (always available)
    return InternalDesigner(ai_provider)


# ── Kept for backward compatibility ───────────────────────────────────────────

def select_design_provider(ai_provider) -> BaseDesigner:
    """Alias for get_active_designer(). Retained for backward compatibility."""
    return get_active_designer(ai_provider)
