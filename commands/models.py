"""Models command — register and manage custom AI models."""
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from services.config_service import get_custom_models, add_custom_model, _load, save_settings
from utils.ui import success, error, info

console = Console()


def show_models_menu() -> None:
    """Display registered custom models and allow adding new ones."""
    while True:
        rprint()
        rprint("[bold bright_white]Manage AI Models[/bold bright_white]")
        rprint("[blue]" + "─" * 47 + "[/blue]")

        # ── 1. List Built-in Models ────────────────────────────────────────────
        built_in_table = Table(title="Built-in Models", show_header=True, header_style="bold yellow", border_style="blue")
        built_in_table.add_column("Model Name", style="bold cyan")
        built_in_table.add_column("Default Provider", style="green")
        built_in_table.add_column("Primary Role", style="white")

        built_in_table.add_row("Qwen 2.5 Coder", "Ollama (fallback OpenRouter)", "Coding / Refactoring")
        built_in_table.add_row("DeepSeek R1", "Ollama (fallback OpenRouter)", "Reasoning / Complex tasks")
        built_in_table.add_row("DeepSeek V3", "OpenRouter", "Assistant / Chat / README")
        built_in_table.add_row("Llama 3.3", "Ollama (fallback OpenRouter)", "Assistant / General tasks")

        console.print(built_in_table)
        rprint()

        # ── 2. List Custom Models ──────────────────────────────────────────────
        customs = get_custom_models()
        if customs:
            custom_table = Table(title="Custom Registered Models", show_header=True, header_style="bold purple", border_style="blue")
            custom_table.add_column("ID", style="bold yellow")
            custom_table.add_column("Provider Name", style="bold cyan")
            custom_table.add_column("Model Name", style="green")
            custom_table.add_column("API Endpoint", style="white")

            for idx, c in enumerate(customs, start=1):
                custom_table.add_row(
                    str(idx),
                    c.get("provider_name", "custom"),
                    c.get("model_name", ""),
                    c.get("api_endpoint", ""),
                )
            console.print(custom_table)
        else:
            rprint("[dim]  No custom models registered yet.[/dim]")

        rprint()
        rprint("[bold white]Options:[/bold white]")
        rprint("  [bold cyan]1[/bold cyan]. Add Custom Model")
        if customs:
            rprint("  [bold cyan]2[/bold cyan]. Delete a Custom Model")
        rprint("  [bold cyan]3[/bold cyan]. Back to GC shell")
        rprint()

        choice = console.input("[bold yellow]Choose option : [/bold yellow]").strip()

        if choice == "1":
            _register_custom_model()
        elif choice == "2" and customs:
            _delete_custom_model(customs)
        elif choice == "3" or choice.lower() in ("exit", "back"):
            break
        else:
            error("Invalid choice.")


def _register_custom_model() -> None:
    """Prompt the user for all custom model details and save them."""
    rprint()
    rprint("[bold purple]Add Custom OpenAI-Compatible Model[/bold purple]")
    rprint("[dim]───────────────────────────────────────────────[/dim]")

    provider_name = console.input("[bold cyan]  Provider Name      : [/bold cyan]").strip()
    if not provider_name:
        error("Provider Name is required.")
        return

    api_endpoint = console.input("[bold cyan]  API Endpoint (URL) : [/bold cyan]").strip()
    if not api_endpoint:
        error("API Endpoint is required.")
        return

    api_key = console.input("[bold cyan]  API Key            : [/bold cyan]").strip()
    model_name = console.input("[bold cyan]  Model Name         : [/bold cyan]").strip()
    if not model_name:
        error("Model Name is required.")
        return

    headers_raw = console.input("[bold cyan]  Headers (JSON / Enter for none) : [/bold cyan]").strip()
    headers = {}
    if headers_raw:
        try:
            headers = json.loads(headers_raw)
        except Exception:
            info("Failed to parse headers JSON, using empty headers.")

    temp_raw = console.input("[bold cyan]  Temperature [/bold cyan][dim](Enter for 0.2)[/dim][bold cyan] : [/bold cyan]").strip()
    temperature = float(temp_raw) if temp_raw else 0.2

    tokens_raw = console.input("[bold cyan]  Max Tokens [/bold cyan][dim](Enter for 2048)[/dim][bold cyan] : [/bold cyan]").strip()
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
    idx_str = console.input("[bold red]Enter the ID of the model to delete : [/bold red]").strip()
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
