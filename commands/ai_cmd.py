"""AI command — enters the GitHub Companion AI agent mode."""
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

console = Console()


def start_ai_mode() -> None:
    """
    Enter the interactive AI > prompt loop.

    The Agent instance is created once and persists for the session,
    preserving conversation memory across multiple turns.
    """
    rprint()
    console.print(Panel(
        "[bold purple]GitHub Companion — AI Agent[/bold purple]\n\n"
        "[white]Speak naturally. The AI will understand and act.\n\n[/white]"
        "[dim]  Examples:\n"
        "    Create a private repo called my-app\n"
        "    Publish my weather project at C:\\projects\\weather\n"
        "    Search my repos for python\n"
        "    Generate a README for this project\n"
        "    What are my latest repositories?\n\n"
        "  Commands:\n"
        "    clear  — reset conversation memory\n"
        "    back   — return to GC shell[/dim]",
        title="[bold purple]🤖 AI Mode[/bold purple]",
        border_style="purple",
        padding=(1, 2),
    ))
    rprint()

    # ── Initialize agent ───────────────────────────────────────────────────────
    try:
        from ai.agent import Agent
        agent = Agent()
    except ValueError as exc:
        # Missing OpenAI key — show a clear, actionable error
        rprint(f"[bold red]❌ Configuration error:[/bold red]")
        rprint(f"[red]   {exc}[/red]")
        return
    except RuntimeError as exc:
        # openai package not installed
        rprint(f"[bold red]❌ Dependency missing:[/bold red] {exc}")
        rprint("[dim]   Run:  pip install openai[/dim]")
        return
    except Exception as exc:
        rprint(f"[bold red]❌ Failed to start AI agent:[/bold red] {exc}")
        return

    rprint()

    # ── Interaction loop ───────────────────────────────────────────────────────
    while True:
        try:
            user_input = console.input("[bold purple]AI > [/bold purple]").strip()
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

        if lower == "help":
            rprint("[dim]  Say anything in natural language. Examples:[/dim]")
            rprint("[dim]    'Create a public repo called demo'[/dim]")
            rprint("[dim]    'List my repositories'[/dim]")
            rprint("[dim]    'Search for flask projects'[/dim]")
            rprint()
            continue

        agent.run(user_input)
        rprint()
