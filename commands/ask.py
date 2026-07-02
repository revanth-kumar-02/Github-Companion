"""Ask command — general AI chatbot mode for questions and explanations."""
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from ai.agent import Agent
from utils.ui import error

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
