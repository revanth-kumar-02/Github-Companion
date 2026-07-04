"""Design Provider Registry for GitHub Companion.

Manages available design providers, interactive selection during
GC > code sessions, and automatic fallback when an external provider
(e.g. Google Stitch) is unavailable.
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


# ── Interactive selection ──────────────────────────────────────────────────────

def select_design_provider(ai_provider) -> BaseDesigner:
    """
    Display the interactive Design Provider selection menu and return
    the chosen (and validated) provider.

    If the selected provider fails health_check(), automatically falls back
    to InternalDesigner with a warning notification.

    Args:
        ai_provider: The active AI BaseProvider (for InternalDesigner).

    Returns:
        A ready-to-use BaseDesigner instance (never None — always falls back).
    """
    from github_companion.services.theme_service import get_active_theme_obj
    theme = get_active_theme_obj()

    providers = get_available_providers()

    rprint()
    rprint(f"[bold {theme.header}]Choose Design Provider[/bold {theme.header}]")
    rprint(f"[{theme.border}]{'─' * 40}[/{theme.border}]")
    rprint()

    for idx, p in enumerate(providers, start=1):
        rec_tag = " [bold yellow]⭐ Recommended[/bold yellow]" if p["recommended"] else ""
        cfg_tag = (
            f" [bold green](Configured)[/bold green]"
            if p["configured"]
            else f" [dim](Not Configured)[/dim]"
        )

        # Stitch-specific: add "not configured" clarification for new users
        extra = ""
        if p["id"] == "stitch" and not p["configured"]:
            extra = "\n     [dim]Run 'auth' → Configure Google Stitch to set up credentials[/dim]"

        rprint(
            f"  [{theme.command}]{idx}[/{theme.command}]. "
            f"[bold white]{p['name']}[/bold white]{cfg_tag}{rec_tag}"
        )
        rprint(f"     [dim]{p['description']}[/dim]{extra}")
        rprint()

    choice = console.input(
        f"[{theme.prompt}]Select Design Provider (1-{len(providers)}) [1]: [{theme.prompt}]"
    ).strip()

    # Default to internal if user presses Enter
    if not choice:
        choice = "1"

    try:
        idx = int(choice)
        if 1 <= idx <= len(providers):
            selected = providers[idx - 1]
        else:
            rprint("[dim]  Invalid choice — defaulting to Internal AI Designer.[/dim]")
            selected = providers[0]
    except ValueError:
        rprint("[dim]  Invalid input — defaulting to Internal AI Designer.[/dim]")
        selected = providers[0]

    provider_id = selected["id"]
    designer = get_provider(provider_id, ai_provider=ai_provider)

    if designer is None:
        rprint("[dim]  Could not instantiate selected provider — defaulting to Internal AI Designer.[/dim]")
        from github_companion.design.internal_designer import InternalDesigner
        return InternalDesigner(ai_provider)

    # ── Health check with automatic fallback ──────────────────────────────────
    if provider_id != "internal":
        rprint()
        with console.status(
            f"[bold yellow]Checking {designer.name} availability...[/bold yellow]",
            spinner="dots",
        ):
            available = designer.health_check()

        if not available:
            rprint()
            rprint(
                f"[bold yellow]⚠  {designer.name} is unavailable.[/bold yellow]"
            )
            rprint(
                "[dim]   Switching to Internal AI Designer. Your coding session will continue normally.[/dim]"
            )
            rprint()
            from github_companion.design.internal_designer import InternalDesigner
            return InternalDesigner(ai_provider)

        rprint(f"[bold green]✓  {designer.name} is connected and ready.[/bold green]")

    rprint(f"[dim]  Design Provider: {designer.name}[/dim]")
    rprint()
    return designer
