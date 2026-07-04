"""Ask command — general AI chatbot mode for questions and explanations."""
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich import print as rprint

from github_companion.ai.agent import Agent
from github_companion.ai.providers.base_provider import BaseProvider
from github_companion.ai.providers.openrouter_provider import OpenRouterProvider
from github_companion.ai.providers.nvidia_provider import NvidiaProvider
from github_companion.ai.providers.ollama_provider import OllamaProvider
from github_companion.services.theme_service import get_active_theme_obj
from github_companion.utils.ui import error, success, show_exception_panel

console = Console()

PROVIDER_DISPLAY_MAP = {
    "openrouter": "OpenRouter",
    "ollama": "Ollama",
    "nvidia": "NVIDIA NIM",
    "openai": "OpenAI API"
}

ASK_SYSTEM_PROMPT = """\
You are GitHub Companion's AI Assistant — a helpful programming chatbot.
You are running in General Assistant Mode.

Your purpose:
- Answer programming questions
- Explain code, Git, and GitHub
- Discuss software architecture
- Provide debugging guidance and explanation

Rules:
- You must act as a chatbot only.
- You do NOT have access to tools.
- You can NEVER write or edit files.
- You can NEVER run terminal commands.
- If asked to perform actions, explain politely that you can only guide the user and that they should use 'code' mode for automated coding/file generation.
- Keep answers clear, readable, and terminal-friendly.
"""


def _select_assistant_model() -> dict | None:
    from github_companion.ai.model_registry import get_models_by_role
    theme = get_active_theme_obj()
    models = get_models_by_role("assistant")
    
    rprint()
    rprint(f"[bold {theme.header}]Assistant Models[/bold {theme.header}]")
    rprint(f"[bold {theme.border}]──────────────────────────────[/bold {theme.border}]")
    
    for idx, m in enumerate(models, start=1):
        rec_prefix = "⭐ " if m.get("recommended") else ""
        rprint(f"  {idx}. {rec_prefix}{m['display_name']}")
        provider_disp = PROVIDER_DISPLAY_MAP.get(m['provider'].lower(), m['provider'].capitalize())
        rprint(f"     Provider : {provider_disp}")
        rprint()
        
    rprint(f"[bold {theme.border}]──────────────────────────────[/bold {theme.border}]")
    rprint("[bold white]Select Model[/bold white]")
    
    while True:
        try:
            choice = console.input(f"[{theme.prompt}]> [/{theme.prompt}]").strip()
        except (KeyboardInterrupt, EOFError):
            return None
            
        if not choice:
            continue
            
        try:
            val = int(choice)
            if 1 <= val <= len(models):
                return models[val - 1]
        except ValueError:
            for m in models:
                if m["display_name"].lower() == choice.lower() or m["model_id"].lower() == choice.lower():
                    return m
        
        error("Invalid selection. Please choose a valid index or name.")


def _display_session_header(model_entry: dict) -> None:
    theme = get_active_theme_obj()
    provider_disp = PROVIDER_DISPLAY_MAP.get(model_entry['provider'].lower(), model_entry['provider'].capitalize())
    
    content = Table.grid(expand=True, padding=(0, 2))
    content.add_column(style=f"bold {theme.highlight}", width=15)
    content.add_column(style="white")
    
    content.add_row("Assistant", "")
    content.add_row("Model", model_entry["display_name"])
    content.add_row("Provider", provider_disp)
    content.add_row("Status", "Ready")
    
    main_group = Table.grid(expand=True)
    main_group.add_row(Text("Assistant Session Started\n", style=f"bold {theme.header}"))
    main_group.add_row(content)
    main_group.add_row(Text("\n──────────────────────────────────────────────", style=theme.border))
    main_group.add_row(Text("\nYou can now ask programming questions.\nType exit to end the assistant session.", style="dim"))
    
    panel = Panel(
        main_group,
        border_style=theme.border,
        box=box.ROUNDED,
        title=f"[bold {theme.header}] 💬 Assistant Session Started [/bold {theme.header}]",
        expand=False
    )
    console.print()
    console.print(panel)
    console.print()


def _get_ollama_with_fallback(model_id: str) -> BaseProvider | None:
    """Check if local Ollama is active, else prompt to retry, configure OpenRouter, or cancel."""
    from github_companion.services.config_service import _load, save_settings, get_ollama_host
    from github_companion.services.setup_wizard import ensure_openrouter_authenticated
    while True:
        ollama = OllamaProvider(model_id, host=get_ollama_host())
        if ollama.health_check():
            return ollama

        rprint(f"\n[bold yellow]Ollama is not installed or offline.[/bold yellow]")
        rprint("Would you like to:")
        rprint("  [bold cyan]1[/bold cyan]. Configure OpenRouter")
        rprint("  [bold cyan]2[/bold cyan]. Retry")
        rprint("  [bold cyan]3[/bold cyan]. Cancel")
        rprint()

        try:
            sub_choice = console.input("[bold purple]> [/bold purple]").strip()
        except (KeyboardInterrupt, EOFError):
            return None
            
        if sub_choice == "1":
            try:
                key = ensure_openrouter_authenticated()
                settings = _load()
                settings["provider"] = "openrouter"
                save_settings(settings)
                return OpenRouterProvider(model_id, api_key=key)
            except Exception as e:
                rprint(f"[bold red]❌ Config error: {e}[/bold red]")
                continue
        elif sub_choice == "2":
            continue
        else:
            return None


def _build_provider_for_model(model_entry: dict) -> BaseProvider | None:
    provider_name = model_entry["provider"].lower()
    model_id = model_entry["model_id"]
    
    if provider_name == "ollama":
        return _get_ollama_with_fallback(model_id)
        
    elif provider_name == "openrouter":
        from github_companion.services.setup_wizard import ensure_openrouter_authenticated
        try:
            key = ensure_openrouter_authenticated()
            return OpenRouterProvider(model_id, api_key=key)
        except Exception as e:
            rprint(f"[bold red]❌ Config error: {e}[/bold red]")
            return None
            
    elif provider_name == "nvidia":
        from github_companion.services.setup_wizard import ensure_nvidia_authenticated
        try:
            key = ensure_nvidia_authenticated()
            return NvidiaProvider(model_id, api_key=key)
        except Exception as e:
            rprint(f"[bold red]❌ Config error: {e}[/bold red]")
            return None
            
    return None


def start_ask_mode() -> None:
    """Enter the interactive Ask > prompt loop with model selection."""
    model_entry = _select_assistant_model()
    if not model_entry:
        return
        
    provider = _build_provider_for_model(model_entry)
    if not provider:
        return
        
    session_start_time = datetime.datetime.now()
    message_count = 0
    
    _display_session_header(model_entry)
    
    try:
        agent = Agent(provider=provider)
    except Exception as exc:
        show_exception_panel(exc, "Failed to start Assistant session")
        return
        
    while True:
        theme = get_active_theme_obj()
        
        elapsed = datetime.datetime.now() - session_start_time
        total_seconds = int(elapsed.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        duration_str = f"{minutes:02d}:{seconds:02d}"
        
        provider_disp = PROVIDER_DISPLAY_MAP.get(model_entry['provider'].lower(), model_entry['provider'].capitalize())
        
        rprint(f"[dim][Model: {model_entry['display_name']} | Provider: {provider_disp} | Messages: {message_count} | Time: {duration_str}][/dim]")
        
        try:
            user_input = console.input(f"[{theme.prompt}]Ask > [/{theme.prompt}]").strip()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]  Ending session...[/dim]")
            break
            
        if not user_input:
            continue
            
        lower = user_input.lower()
        
        if lower in ("exit", "quit", "back"):
            rprint("[dim]  Ending session...[/dim]")
            break
            
        if lower == "clear":
            agent.memory.clear()
            message_count = 0
            session_start_time = datetime.datetime.now()
            rprint("[dim]  ✔ Conversation memory cleared.[/dim]")
            rprint()
            continue
            
        if lower == "/model":
            new_model_entry = _select_assistant_model()
            if new_model_entry:
                new_provider = _build_provider_for_model(new_model_entry)
                if new_provider:
                    model_entry = new_model_entry
                    provider = new_provider
                    agent.provider = new_provider
                    rprint(f"[bold green]✓ Switched to model {model_entry['display_name']}[/bold green]")
                    _display_session_header(model_entry)
            continue
            
        try:
            agent.run(user_input, system_prompt=ASK_SYSTEM_PROMPT, enable_tools=False)
            message_count += 1
        except Exception as e:
            show_exception_panel(e, "Error during query execution")
        rprint()


def start_chat_mode() -> None:
    """Invokes the standard ask mode with model selection for visual consistency."""
    start_ask_mode()
