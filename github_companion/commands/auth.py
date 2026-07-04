"""Auth command — configure and verify GitHub and AI provider credentials."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from github_companion.services.config_service import _load, save_settings
from github_companion.services.setup_wizard import (
    get_masked_input,
    _validate_github_credentials,
    _validate_openrouter_key,
    _validate_nvidia_key,
)
from github_companion.services.config_service import get_nvidia_api_key
from github_companion.utils.ui import success, error, info, warning

console = Console()


def auth_cmd() -> None:
    """Interactive authentication command loop."""
    from github_companion.services.theme_service import get_active_theme_obj
    from rich import box
    while True:
        theme = get_active_theme_obj()
        settings = _load()
        gh_user = settings.get("github_username", "")
        gh_tok = settings.get("github_token", "")
        or_key = settings.get("openrouter_api_key", "")
        nv_key = settings.get("nvidia_api_key", "")

        gh_status = "[bold green]✓ Connected[/bold green]" if (gh_user and gh_tok) else "[bold red]✗ Not Configured[/bold red]"
        or_status = "[bold green]✓ Connected[/bold green]" if or_key else "[bold red]✗ Not Configured[/bold red]"
        nv_status = "[bold green]✓ Connected[/bold green]" if nv_key else "[bold red]✗ Not Configured[/bold red]"

        content = []
        content.append(f"  GitHub      : {gh_status}")
        content.append(f"  OpenRouter  : {or_status}")
        content.append(f"  NVIDIA NIM  : {nv_status}")
        content.append("")
        content.append("[bold white]Options:[/bold white]")
        content.append(f"  [{theme.command}]1[/{theme.command}]. Configure GitHub")
        content.append(f"  [{theme.command}]2[/{theme.command}]. Configure OpenRouter")
        content.append(f"  [{theme.command}]3[/{theme.command}]. Configure NVIDIA NIM")
        content.append(f"  [{theme.command}]4[/{theme.command}]. Test Connections")
        content.append(f"  [{theme.command}]5[/{theme.command}]. Remove Credentials")
        content.append(f"  [{theme.command}]6[/{theme.command}]. Back to GC shell")
        
        console.print()
        console.print(f"[bold {theme.header}]Authentication Management[/bold {theme.header}]")
        console.print("─" * 40, style=theme.border)
        console.print()
        console.print("\n".join(content))
        console.print()

        choice = console.input(f"[{theme.prompt}]Select option (1-6) : [/{theme.prompt}]").strip()

        if choice == "1":
            _configure_github()
        elif choice == "2":
            _configure_openrouter()
        elif choice == "3":
            _configure_nvidia_nim()
        elif choice == "4":
            _test_connections()
        elif choice == "5":
            _remove_credentials()
        elif choice == "6" or choice.lower() in ("exit", "back"):
            break
        else:
            error("Invalid choice.")


def _configure_github() -> None:
    """Prompt and validate GitHub credentials."""
    rprint()
    username = console.input("[bold cyan]  GitHub Username             : [/bold cyan]").strip()
    token = get_masked_input("[bold cyan]  GitHub Personal Access Token : [/bold cyan]")

    if not username or not token:
        error("Username and Token are required.")
        return

    with console.status("[bold yellow]  Validating GitHub credentials...[/bold yellow]", spinner="dots"):
        valid, msg = _validate_github_credentials(username, token)

    if valid:
        settings = _load()
        settings["github_username"] = username
        settings["github_token"] = token
        save_settings(settings)
        success("GitHub credentials saved successfully.")
    else:
        error(f"Validation failed: {msg}")


def _configure_openrouter() -> None:
    """Prompt and validate OpenRouter API Key."""
    rprint()
    key = get_masked_input("[bold cyan]  OpenRouter API Key : [/bold cyan]")
    if not key:
        error("API Key is required.")
        return

    with console.status("[bold yellow]  Validating OpenRouter Key...[/bold yellow]", spinner="dots"):
        valid = _validate_openrouter_key(key)

    if valid:
        settings = _load()
        settings["openrouter_api_key"] = key
        save_settings(settings)
        success("OpenRouter Connected & API Key Verified.")
    else:
        error("Invalid OpenRouter API Key.")


def _configure_nvidia_nim() -> None:
    """Prompt and validate NVIDIA API Key."""
    rprint()
    key = get_masked_input("[bold cyan]  NVIDIA API Key : [/bold cyan]")
    if not key:
        error("API Key is required.")
        return

    with console.status("[bold yellow]  Validating NVIDIA Key...[/bold yellow]", spinner="dots"):
        valid = _validate_nvidia_key(key)

    if valid:
        settings = _load()
        settings["nvidia_api_key"] = key
        save_settings(settings)
        success("NVIDIA Connected & API Key Verified.")
    else:
        error("Invalid NVIDIA API Key.")


def _test_connections() -> None:
    """Test connections to GitHub, OpenRouter, and NVIDIA NIM APIs."""
    rprint()
    settings = _load()
    gh_user = settings.get("github_username", "")
    gh_tok = settings.get("github_token", "")
    or_key = settings.get("openrouter_api_key", "")
    nv_key = settings.get("nvidia_api_key", "")

    # GitHub
    if gh_user and gh_tok:
        with console.status("[bold yellow]Testing GitHub Connection...[/bold yellow]", spinner="dots"):
            valid, msg = _validate_github_credentials(gh_user, gh_tok)
        if valid:
            success(f"GitHub: Connected as '{gh_user}'")
        else:
            error(f"GitHub: Connection failed: {msg}")
    else:
        warning("GitHub: Not configured")

    # OpenRouter
    if or_key:
        with console.status("[bold yellow]Testing OpenRouter Connection...[/bold yellow]", spinner="dots"):
            valid = _validate_openrouter_key(or_key)
        if valid:
            success("OpenRouter: Connection successful")
        else:
            error("OpenRouter: API Key validation failed")
    else:
        warning("OpenRouter: Not configured")

    # NVIDIA NIM
    if nv_key:
        with console.status("[bold yellow]Testing NVIDIA NIM Connection...[/bold yellow]", spinner="dots"):
            valid = _validate_nvidia_key(nv_key)
        if valid:
            success("NVIDIA NIM: Connection successful")
        else:
            error("NVIDIA NIM: API Key validation failed")
    else:
        warning("NVIDIA NIM: Not configured")


def _remove_credentials() -> None:
    """Remove user credentials interactively."""
    rprint()
    rprint("[bold red]Remove Credentials[/bold red]")
    rprint("  [bold cyan]1[/bold cyan]. Remove GitHub credentials")
    rprint("  [bold cyan]2[/bold cyan]. Remove OpenRouter credentials")
    rprint("  [bold cyan]3[/bold cyan]. Remove NVIDIA NIM credentials")
    rprint("  [bold cyan]4[/bold cyan]. Remove All")
    rprint("  [bold cyan]5[/bold cyan]. Cancel")
    rprint()

    choice = console.input("[bold yellow]Select option (1-5) : [/bold yellow]").strip()
    settings = _load()

    if choice == "1":
        settings["github_username"] = ""
        settings["github_token"] = ""
        save_settings(settings)
        success("GitHub credentials removed.")
    elif choice == "2":
        settings["openrouter_api_key"] = ""
        save_settings(settings)
        success("OpenRouter key removed.")
    elif choice == "3":
        settings["nvidia_api_key"] = ""
        save_settings(settings)
        success("NVIDIA NIM key removed.")
    elif choice == "4":
        settings["github_username"] = ""
        settings["github_token"] = ""
        settings["openrouter_api_key"] = ""
        settings["nvidia_api_key"] = ""
        save_settings(settings)
        success("All credentials removed.")
    else:
        rprint("[dim]  Cancelled.[/dim]")
