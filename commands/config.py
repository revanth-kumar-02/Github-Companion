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
    elif subcommand == "ai":
        _config_ai()
    elif subcommand == "workspace":
        _config_workspace()
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

    token = console.input("[bold cyan]  GitHub Token [/bold cyan][dim](Enter to keep current)[/dim] : ").strip()
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
        key = console.input("[bold cyan]  OpenRouter API Key [/bold cyan][dim](Enter to keep current)[/dim] : ").strip()
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


def _config_ai() -> None:
    """Interactive AI Configuration editor (config ai)."""
    while True:
        settings = _load()
        provider = settings.get("provider", "ollama")
        or_key = settings.get("openrouter_api_key", "")
        coding_model = settings.get("coding_model", "qwen2.5-coder")

        masked_key = "Not Configured"
        if or_key:
            masked_key = or_key[:6] + "*" * (len(or_key) - 6) if len(or_key) > 6 else "*" * 8

        rprint()
        rprint("[bold bright_white]AI Configuration[/bold bright_white]")
        rprint("[blue]" + "─" * 47 + "[/blue]")
        rprint(f"  Provider              : {provider.capitalize()}")
        rprint(f"  API Key               : {masked_key}")
        rprint(f"  Default Coding Model  : {coding_model}")
        rprint()

        rprint("[bold white]Options:[/bold white]")
        rprint("  [bold cyan]1[/bold cyan]. Change Provider")
        rprint("  [bold cyan]2[/bold cyan]. Change API Key")
        rprint("  [bold cyan]3[/bold cyan]. Change Default Model")
        rprint("  [bold cyan]4[/bold cyan]. Remove API Key")
        rprint("  [bold cyan]5[/bold cyan]. Back to GC shell")
        rprint()

        choice = console.input("[bold yellow]Select option (1-5) : [/bold yellow]").strip()

        if choice == "1":
            rprint("\nSelect Provider:")
            rprint("  1. Ollama")
            rprint("  2. OpenRouter")
            p_choice = console.input("> ").strip()
            if p_choice == "1":
                settings["provider"] = "ollama"
            elif p_choice == "2":
                settings["provider"] = "openrouter"
            save_settings(settings)
            success("Provider updated.")
        elif choice == "2":
            from services.setup_wizard import get_masked_input, _validate_openrouter_key
            new_key = get_masked_input("\nEnter OpenRouter API Key: ")
            if new_key:
                with console.status("[bold yellow]Validating Key...[/bold yellow]", spinner="dots"):
                    valid = _validate_openrouter_key(new_key)
                if valid:
                    settings["openrouter_api_key"] = new_key
                    save_settings(settings)
                    success("OpenRouter key saved.")
                else:
                    error("Invalid OpenRouter API key.")
        elif choice == "3":
            rprint("\nSelect Default Coding Model:")
            rprint("  1. Qwen 2.5 Coder")
            rprint("  2. DeepSeek V3")
            rprint("  3. DeepSeek R1")
            rprint("  4. Llama 3.3")
            m_choice = console.input("> ").strip()
            models_map = {
                "1": "qwen2.5-coder",
                "2": "deepseek-v3",
                "3": "deepseek-r1",
                "4": "llama3.3"
            }
            if m_choice in models_map:
                settings["coding_model"] = models_map[m_choice]
                save_settings(settings)
                success(f"Default coding model set to {models_map[m_choice]}.")
            else:
                error("Invalid choice.")
        elif choice == "4":
            settings["openrouter_api_key"] = ""
            save_settings(settings)
            success("OpenRouter key removed.")
        elif choice == "5" or choice.lower() in ("exit", "back"):
            break
        else:
            error("Invalid choice.")


def _config_workspace() -> None:
    """Interactive settings view and modification of the default project workspace path."""
    while True:
        settings = _load()
        current_ws = settings.get("workspace", "")

        rprint()
        rprint("[bold bright_white]Workspace Configuration[/bold bright_white]")
        rprint("[blue]" + "─" * 47 + "[/blue]")
        rprint(f"  Current Workspace : {current_ws or 'Not Set (Defaults to current working directory)'}")
        rprint()

        rprint("[bold white]Options:[/bold white]")
        rprint("  [bold cyan]1[/bold cyan]. Change Workspace")
        rprint("  [bold cyan]2[/bold cyan]. Reset Workspace")
        rprint("  [bold cyan]3[/bold cyan]. Back to GC shell")
        rprint()

        choice = console.input("[bold yellow]Select option (1-3) : [/bold yellow]").strip()

        if choice == "1":
            new_ws = console.input("\nEnter new workspace directory path: ").strip()
            if new_ws:
                resolved_path = os.path.abspath(os.path.expanduser(new_ws))
                if not os.path.exists(resolved_path):
                    rprint(f"[bold yellow]Directory '{resolved_path}' does not exist.[/bold yellow]")
                    create = console.input("Create it? (y/n) : ").strip().lower()
                    if create == "y":
                        try:
                            os.makedirs(resolved_path, exist_ok=True)
                            success(f"Directory '{resolved_path}' created.")
                        except Exception as e:
                            error(f"Failed to create directory: {e}")
                            continue
                    else:
                        rprint("[dim]  Cancelled workspace update.[/dim]")
                        continue
                
                settings["workspace"] = resolved_path
                save_settings(settings)
                success(f"Workspace path updated and saved successfully.")
        elif choice == "2":
            settings["workspace"] = ""
            save_settings(settings)
            success("Workspace path reset to default.")
        elif choice == "3" or choice.lower() in ("exit", "back"):
            break
        else:
            error("Invalid choice.")


