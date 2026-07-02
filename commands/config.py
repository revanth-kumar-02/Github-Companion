"""Config command — display, edit, or reset configuration."""
import os
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from services.config_service import CONFIG_PATH, _load, save_settings
from services.setup_wizard import run_setup_wizard
from utils.ui import success, error, info

console = Console()


def config_cmd(args: list[str] = None) -> None:
    """
    Main entry point for config command.
    Accepts list of arguments (e.g. ['edit'] or ['reset']).
    """
    if not args:
        _display_config()
        return

    subcommand = args[0].lower()

    if subcommand == "edit":
        _edit_config()
    elif subcommand == "reset":
        _reset_config()
    else:
        _display_config()


def _display_config() -> None:
    """Display the current configuration in a beautiful table."""
    settings = _load()
    if not settings:
        error("No configuration found. Run 'gc' or restart to configure.")
        return

    rprint()
    rprint("[bold bright_white]Current Configuration[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    table = Table(show_header=True, header_style="bold yellow", border_style="blue")
    table.add_column("Setting", style="bold cyan")
    table.add_column("Value", style="white")

    # Display settings, masking sensitive tokens
    for k, v in settings.items():
        if k in ("github_token", "openrouter_api_key", "api_key") and v:
            # Mask the token
            masked = v[:6] + "*" * (len(v) - 6) if len(v) > 6 else "*" * 8
            table.add_row(k, masked)
        elif k == "custom_models":
            table.add_row(k, f"{len(v)} custom model(s) registered")
        else:
            table.add_row(k, str(v))

    console.print(table)
    rprint(f"\n[dim]Configuration file location: {CONFIG_PATH}[/dim]")
    rprint("[dim]Use 'config edit' to edit or 'config reset' to reset settings.[/dim]\n")


def _edit_config() -> None:
    """Prompt user to interactively edit configuration values."""
    settings = _load()
    rprint()
    rprint("[bold bright_white]Interactive Configuration Editor[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    # Edit GitHub details
    username = console.input(f"[bold cyan]  GitHub Username [/bold cyan][dim]({settings.get('github_username', '')})[/dim] : ").strip()
    if username:
        settings["github_username"] = username

    token = console.input("[bold cyan]  GitHub Token [/bold cyan][dim](Enter to keep current)[/dim] : ", password=True).strip()
    if token:
        settings["github_token"] = token

    # Edit AI details
    provider = console.input(f"[bold cyan]  AI Provider [/bold cyan][dim]({settings.get('provider', 'ollama')})[/dim] : ").strip()
    if provider:
        settings["provider"] = provider.lower()

    coding = console.input(f"[bold cyan]  Coding Model [/bold cyan][dim]({settings.get('coding_model', 'qwen2.5-coder')})[/dim] : ").strip()
    if coding:
        settings["coding_model"] = coding

    reasoning = console.input(f"[bold cyan]  Reasoning Model [/bold cyan][dim]({settings.get('reasoning_model', 'deepseek-r1')})[/dim] : ").strip()
    if reasoning:
        settings["reasoning_model"] = reasoning

    assistant = console.input(f"[bold cyan]  Assistant Model [/bold cyan][dim]({settings.get('assistant_model', 'llama3.3')})[/dim] : ").strip()
    if assistant:
        settings["assistant_model"] = assistant

    # Provider specific
    if settings.get("provider") == "ollama":
        host = console.input(f"[bold cyan]  Ollama Host [/bold cyan][dim]({settings.get('ollama_host', 'http://localhost:11434')})[/dim] : ").strip()
        if host:
            settings["ollama_host"] = host
    elif settings.get("provider") == "openrouter":
        key = console.input("[bold cyan]  OpenRouter API Key [/bold cyan][dim](Enter to keep current)[/dim] : ", password=True).strip()
        if key:
            settings["openrouter_api_key"] = key

    save_settings(settings)
    success("Configuration updated and saved successfully.")


def _reset_config() -> None:
    """Delete configuration file and restart Setup Wizard."""
    rprint()
    confirm = console.input("[bold red]Are you sure you want to delete all settings and reset? (y/n) : [/bold red]").strip().lower()
    if confirm != "y":
        rprint("[dim]  Cancelled.[/dim]")
        return

    if CONFIG_PATH.exists():
        try:
            os.remove(CONFIG_PATH)
            success("Configuration deleted successfully.")
        except Exception as e:
            error(f"Failed to delete configuration file: {e}")
            return
    else:
        info("No configuration file found to delete.")

    rprint("[bold yellow]Starting Setup Wizard...[/bold yellow]")
    run_setup_wizard()
