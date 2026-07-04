"""Models command — register and manage custom AI models."""
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from github_companion.services.config_service import get_custom_models, add_custom_model, _load, save_settings
from github_companion.services.theme_service import get_active_theme_obj
from github_companion.utils.ui import success, error, info
from github_companion.ai.model_registry import MODELS

console = Console()

ROLE_MAP = {
    "coding": "Coding / Refactoring",
    "planning": "Reasoning / Complex tasks",
    "assistant": "Assistant / Discussion",
    "review": "Code Review"
}

PROVIDER_MAP = {
    "ollama": "Ollama (fallback OpenRouter)",
    "openrouter": "OpenRouter",
    "nvidia": "NVIDIA NIM Cloud",
    "openai": "OpenAI API"
}


def show_models_menu() -> None:
    """Display registered custom models and allow adding new ones."""
    while True:
        theme = get_active_theme_obj()
        header_style = theme.table_header
        border_style = theme.border
        from rich import box

        rprint()
        rprint(f"[{theme.header}]Manage AI Models[/{theme.header}]")
        rprint(f"[{theme.border}]" + "─" * 47 + f"[/{theme.border}]")

        # ── 1. List Built-in Models ────────────────────────────────────────────
        built_in_table = Table(show_header=True, header_style=header_style, border_style=border_style)
        built_in_table.add_column("Model Name", style=theme.command)
        built_in_table.add_column("Default Provider", style=theme.highlight)
        built_in_table.add_column("Primary Role", style=theme.description)

        for m in MODELS:
            display_name = m.get("display_name", "")
            provider = m.get("provider", "")
            role = m.get("role", "")
            
            provider_str = PROVIDER_MAP.get(provider.lower(), provider.capitalize())
            role_str = ROLE_MAP.get(role.lower(), role.capitalize())
            
            if m.get("recommended"):
                display_name_str = f"{display_name} (Recommended)"
            else:
                display_name_str = display_name
                
            built_in_table.add_row(display_name_str, provider_str, role_str)

        console.print(f"[bold {theme.header}]Built-in Models[/bold {theme.header}]")
        console.print(built_in_table)
        rprint()

        # ── 2. List Custom Models ──────────────────────────────────────────────
        customs = get_custom_models()
        if customs:
            custom_table = Table(show_header=True, header_style=header_style, border_style=border_style)
            custom_table.add_column("ID", style=theme.highlight)
            custom_table.add_column("Provider Name", style=theme.command)
            custom_table.add_column("Model Name", style=theme.description)
            custom_table.add_column("API Endpoint", style=theme.description)

            for idx, c in enumerate(customs, start=1):
                custom_table.add_row(
                    str(idx),
                    c.get("provider_name", "custom"),
                    c.get("model_name", ""),
                    c.get("api_endpoint", ""),
                )
            console.print(f"[bold {theme.header}]Custom Registered Models[/bold {theme.header}]")
            console.print(custom_table)
        else:
            rprint("[dim]  No custom models registered yet.[/dim]")

        rprint()
        options = []
        options.append(f"  [{theme.highlight}]1[/{theme.highlight}]. Add Custom Model")
        if customs:
            options.append(f"  [{theme.highlight}]2[/{theme.highlight}]. Delete a Custom Model")
            options.append(f"  [{theme.highlight}]3[/{theme.highlight}]. Back to GC shell")
        else:
            options.append(f"  [{theme.highlight}]2[/{theme.highlight}]. Back to GC shell")
            
        rprint("[bold white]Options:[/bold white]")
        for opt in options:
            rprint(opt)
        rprint()

        try:
            choice = console.input(f"[{theme.prompt}]Choose option : [/{theme.prompt}]").strip()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]  Cancelled.[/dim]")
            break

        if choice == "1":
            _register_custom_model()
        elif choice == "2":
            if customs:
                _delete_custom_model(customs)
            else:
                break
        elif choice == "3" and customs:
            break
        elif choice.lower() in ("exit", "back"):
            break
        else:
            error("Invalid choice.")


def _register_custom_model() -> None:
    """Prompt the user for all custom model details and save them."""
    theme = get_active_theme_obj()
    rprint()
    rprint(f"[bold {theme.highlight}]Add Custom OpenAI-Compatible Model[/bold {theme.highlight}]")
    rprint(f"[{theme.border}]───────────────────────────────────────────────[/{theme.border}]")

    provider_name = console.input(f"[{theme.prompt}]  Provider Name      : [/{theme.prompt}]").strip()
    if not provider_name:
        error("Provider Name is required.")
        return

    api_endpoint = console.input(f"[{theme.prompt}]  API Endpoint (URL) : [/{theme.prompt}]").strip()
    if not api_endpoint:
        error("API Endpoint is required.")
        return

    api_key = console.input(f"[{theme.prompt}]  API Key            : [/{theme.prompt}]").strip()
    model_name = console.input(f"[{theme.prompt}]  Model Name         : [/{theme.prompt}]").strip()
    if not model_name:
        error("Model Name is required.")
        return

    headers_raw = console.input(f"[{theme.prompt}]  Headers (JSON / Enter for none) : [/{theme.prompt}]").strip()
    headers = {}
    if headers_raw:
        try:
            headers = json.loads(headers_raw)
        except Exception:
            info("Failed to parse headers JSON, using empty headers.")

    temp_raw = console.input(f"[{theme.prompt}]  Temperature [/[{theme.prompt}]][dim](Enter for 0.2)[/dim][{theme.prompt}] : [/{theme.prompt}]").strip()
    temperature = float(temp_raw) if temp_raw else 0.2

    tokens_raw = console.input(f"[{theme.prompt}]  Max Tokens [/[{theme.prompt}]][dim](Enter for 2048)[/dim][{theme.prompt}] : [/{theme.prompt}]").strip()
    max_tokens = int(tokens_raw) if tokens_raw else 2048

    model_config = {
        "provider_name": provider_name,
        "api_endpoint": api_endpoint,
        "api_key": api_key,
        "model_name": model_name,
        "headers": headers,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    add_custom_model(model_config)
    success(f"Custom model '{model_name}' registered successfully.")


def _delete_custom_model(customs: list[dict]) -> None:
    """Prompt to delete a registered custom model."""
    theme = get_active_theme_obj()
    idx_str = console.input(f"[{theme.error}]Enter the ID of the model to delete : [/{theme.error}]").strip()
    try:
        idx = int(idx_str) - 1
        if 0 <= idx < len(customs):
            deleted = customs.pop(idx)
            settings = _load()
            settings["custom_models"] = customs
            save_settings(settings)
            success(f"Deleted custom model '{deleted.get('model_name')}' successfully.")
        else:
            error("Invalid ID.")
    except Exception:
        error("Invalid input.")
