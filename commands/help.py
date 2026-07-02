"""Help command — displays all available GitHub Companion commands."""
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


def show_help():
    rprint()
    rprint("[bold bright_white]GitHub Companion — Available Commands[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint()

    table = Table(
        show_header=True,
        header_style="bold bright_white on #1a1a2e",
        border_style="blue",
        row_styles=["", "dim"],
        padding=(0, 2),
        expand=False,
    )

    table.add_column("Command",     style="bold cyan",    no_wrap=True, min_width=12)
    table.add_column("Category",   style="bold yellow",  no_wrap=True, min_width=14)
    table.add_column("Description",style="white",        no_wrap=False, min_width=36)

    rows = [
        # Info commands
        ("profile",   "GitHub",       "Show your GitHub profile details"),
        ("repos",     "GitHub",       "List all your repositories"),
        ("latest",    "GitHub",       "Show the latest created repository"),
        ("pushed",    "GitHub",       "Show the most recently pushed repository"),
        ("heatmap",   "GitHub",       "Display your contribution heatmap"),
        # Repo management
        ("create",    "Repository",   "Create a new GitHub repository"),
        ("delete",    "Repository",   "Delete an existing GitHub repository"),
        ("rename",    "Repository",   "Rename a GitHub repository"),
        ("publish",   "Repository",   "Publish a local project folder to GitHub"),
        # Utilities
        ("search",    "Utility",      "Search your repositories by keyword"),
        ("readme",    "Utility",      "Interactively generate a README.md file"),
        # AI Agent
        ("ai",        "AI Agent",     "Enter AI mode — use natural language to take actions"),
        # System
        ("version",   "System",       "Show installed Git version"),
        ("status",    "System",       "Show current Git status"),
        ("help",      "System",       "Show this help table"),
        ("exit",      "System",       "Exit the interactive shell"),
    ]

    for cmd, category, desc in rows:
        table.add_row(cmd, category, desc)

    console.print(table)
    rprint()
    rprint("[dim]  Run[/dim] [bold cyan]gc[/bold cyan] [dim]to enter the interactive shell, or[/dim] [bold cyan]python app.py <command>[/bold cyan] [dim]to run directly.[/dim]")
    rprint()