"""Help command — displays all available GitHub Companion commands."""
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


def show_help():
    from github_companion.services.theme_service import get_active_theme_obj
    theme = get_active_theme_obj()
    header_style = theme.table_header
    border_style = theme.border
    category_styles = theme.category_colors

    rprint()
    rprint(f"[{theme.header}]GitHub Companion — Available Commands[/{theme.header}]")
    rprint(f"[{border_style}]" + "─" * 47 + f"[/{border_style}]")
    rprint()

    table = Table(
        show_header=True,
        header_style=header_style,
        border_style=border_style,
        padding=(0, 1),
        expand=False,
    )

    table.add_column("Command",     no_wrap=True, width=12)
    table.add_column("Category",   no_wrap=True, width=14)
    table.add_column("Description",style=theme.description,              no_wrap=False, width=50)

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
        ("clone",     "Repository",   "Clone a remote GitHub repository locally"),
        # Utilities
        ("search",    "Utility",      "Search your repositories by keyword"),
        ("readme",    "Utility",      "Interactively generate a README.md file"),
        # AI Agent
        ("ai",        "AI Agent",     "Enter AI mode — use natural language to take actions"),
        ("ask",       "AI Agent",     "General AI assistant chatbot (no file edits/commands)"),
        ("code",      "AI Agent",     "Autonomous AI Coding Agent (planning + generation)"),
        ("models",    "AI Agent",     "Register and manage custom AI models"),
        # Workspace
        ("workspace", "Workspace",    "Manage default GC-Projects workspace location"),
        ("projects",  "Workspace",    "Manage and run generated projects in GC-Projects"),
        ("theme",     "Workspace",    "Configure visual color theme presets"),
        # System
        ("auth",      "System",       "Manage GitHub and OpenRouter authentication credentials"),
        ("login",     "System",       "Reconfigure GitHub credentials"),
        ("logout",    "System",       "Remove GitHub credentials"),
        ("config",    "System",       "Display current settings. Try: 'config edit', 'config reset', 'config ai', 'config workspace'"),
        ("doctor",    "System",       "Diagnose Git, GitHub, Internet, and AI. Try: 'doctor ai'"),
        ("tutor",     "System",       "Start interactive step-by-step developer tutorial"),

        ("version",   "System",       "Show installed Git version"),
        ("status",    "System",       "Show current Git status"),
        ("help",      "System",       "Show this help table"),
        ("exit",      "System",       "Exit the interactive shell"),
    ]

    last_category = None
    for cmd, category, desc in rows:
        if last_category is not None and category != last_category:
            table.add_row("", "", "")
        
        style = category_styles.get(category, "white")
        styled_cmd = f"[{style}]{cmd}[/{style}]"
        styled_category = f"[{style}]{category}[/{style}]"
        
        table.add_row(styled_cmd, styled_category, desc)
        last_category = category

    console.print(table)
    rprint()
    rprint(f"[dim]  Run[/dim] [{theme.highlight}]gc[/{theme.highlight}] [dim]to enter the interactive shell.[/dim]")
    rprint()