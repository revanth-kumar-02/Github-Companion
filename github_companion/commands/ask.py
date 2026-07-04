"""Ask command — general AI chatbot mode for questions and explanations."""
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from github_companion.ai.agent import Agent
from github_companion.ai.providers.base_provider import BaseProvider
from github_companion.ai.providers.openrouter_provider import OpenRouterProvider
from github_companion.ai.providers.nvidia_provider import NvidiaProvider
from github_companion.utils.ui import error, success

console = Console()

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


def start_ask_mode() -> None:
    """Enter the interactive Ask > prompt loop."""
    rprint()
    console.print(Panel(
        "[bold purple]GitHub Companion — Ask Mode[/bold purple]\n\n"
        "[white]Ask programming questions, discuss architecture, or ask for explanations.\n"
        "This mode behaves like a chatbot and [bold red]never edits files or runs commands.[/bold red]\n\n[/white]"
        "[dim]  Examples:\n"
        "    How does git rebase work?\n"
        "    Explain the MVC design pattern\n"
        "    What is a class in Python?\n\n"
        "  Commands:\n"
        "    clear  — reset conversation memory\n"
        "    back   — return to GC shell[/dim]",
        title="[bold purple]💬 Ask Mode (Chatbot)[/bold purple]",
        border_style="purple",
        padding=(1, 2),
    ))
    rprint()

    try:
        agent = Agent()
    except Exception as exc:
        rprint(f"[bold red]❌ Failed to start Ask mode:[/bold red] {exc}")
        return

    while True:
        try:
            user_input = console.input("[bold purple]Ask > [/bold purple]").strip()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]  Returning to GC shell...[/dim]")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("exit", "quit", "back"):
            rprint("[dim]  Returning to GC shell...[/dim]")
            break

        if lower == "clear":
            agent.memory.clear()
            rprint("[dim]  ✔ Conversation memory cleared.[/dim]")
            rprint()
            continue

        # Run the agent with enable_tools=False so it cannot make tool calls
        agent.run(user_input, system_prompt=ASK_SYSTEM_PROMPT, enable_tools=False)
        rprint()


def _build_provider_for_model(model_entry: dict) -> BaseProvider | None:
    provider_name = model_entry["provider"].lower()
    model_id = model_entry["model_id"]
    
    if provider_name == "ollama":
        from github_companion.services.config_service import get_ollama_host
        from github_companion.ai.providers.ollama_provider import OllamaProvider
        return OllamaProvider(model_name=model_id, host=get_ollama_host())
        
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


def start_chat_mode() -> None:
    """Choose assistant model and launch chat session (GC > chat)."""
    from github_companion.ai.model_registry import get_models_by_role
    rprint()
    rprint("[bold bright_white]Assistant Models[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    
    models = get_models_by_role("assistant")
    for idx, m in enumerate(models, start=1):
        rec_tag = " ⭐ [dim]Recommended[/dim]" if m.get("recommended") else ""
        rprint(f"  [bold cyan]{idx}[/bold cyan]. {m['display_name']} (Provider: {m['provider'].upper()}){rec_tag}")
        
    rprint()
    choice = console.input("[bold yellow]Select assistant model number : [/bold yellow]").strip()
    
    try:
        val = int(choice)
        if 1 <= val <= len(models):
            selected_provider = _build_provider_for_model(models[val - 1])
        else:
            error("Invalid selection.")
            return
    except ValueError:
        error("Invalid selection.")
        return

    if not selected_provider:
        return

    rprint(f"[dim]  Selected: {selected_provider.name} ({selected_provider.model})[/dim]\n")

    # Enter Chat / Ask Mode with the selected provider
    console.print(Panel(
        f"[bold purple]GitHub Companion — Chat Mode ({selected_provider.name})[/bold purple]\n\n"
        "[white]Ask programming questions, discuss architecture, or ask for explanations.\n"
        "This mode behaves like a chatbot and [bold red]never edits files or runs commands.[/bold red]\n\n[/white]"
        "[dim]  Commands:\n"
        "    clear  — reset conversation memory\n"
        "    back   — return to GC shell[/dim]",
        title="[bold purple]💬 Chat Mode[/bold purple]",
        border_style="purple",
        padding=(1, 2),
    ))
    rprint()

    try:
        agent = Agent(provider=selected_provider)
    except Exception as exc:
        rprint(f"[bold red]❌ Failed to start Chat mode:[/bold red] {exc}")
        return

    while True:
        try:
            user_input = console.input("[bold purple]Chat > [/bold purple]").strip()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]  Returning to GC shell...[/dim]")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("exit", "quit", "back"):
            rprint("[dim]  Returning to GC shell...[/dim]")
            break

        if lower == "clear":
            agent.memory.clear()
            rprint("[dim]  ✔ Conversation memory cleared.[/dim]")
            rprint()
            continue

        agent.run(user_input, system_prompt=ASK_SYSTEM_PROMPT, enable_tools=False)
        rprint()

