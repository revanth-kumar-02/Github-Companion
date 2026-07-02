"""Search command — search the authenticated user's GitHub repositories."""
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from datetime import datetime

from services.github_service import search_repositories
from utils.ui import error, warning

console = Console()


def _format_date(iso_str: str) -> str:
    """Convert ISO 8601 date string to a clean readable format."""
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d %b %Y")
    except Exception:
        return iso_str or "—"


def gc_search():
    rprint()
    rprint("[bold bright_white]Search Repositories[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    keyword = console.input("[bold cyan]  Keyword : [/bold cyan]").strip()

    if not keyword:
        warning("Please enter a keyword to search.")
        return

    with console.status(f"[bold yellow]  Searching for '{keyword}'...[/bold yellow]"):
        response = search_repositories(keyword)

    if response.status_code != 200:
        error("Failed to search repositories.")
        err_msg = response.json().get("message", "Unknown error")
        rprint(f"[dim red]  → {err_msg}[/dim red]")
        return

    data  = response.json()
    repos = data.get("items", [])
    total = data.get("total_count", 0)

    if not repos:
        warning(f"No repositories found matching '{keyword}'.")
        return

    rprint()
    rprint(f"[dim]  Found [bold]{min(total, 30)}[/bold] result(s) for '[cyan]{keyword}[/cyan]'[/dim]")
    rprint()

    # ── Build Rich Table ────────────────────────────────────────────────────
    table = Table(
        show_header=True,
        header_style="bold bright_white on #1a1a2e",
        border_style="blue",
        row_styles=["", "dim"],
        padding=(0, 1),
        expand=False,
    )

    table.add_column("Repository",  style="bold cyan",    no_wrap=True,  min_width=24)
    table.add_column("Visibility",  style="bold",         no_wrap=True,  min_width=10, justify="center")
    table.add_column("Language",    style="yellow",       no_wrap=True,  min_width=14)
    table.add_column("⭐ Stars",    style="bold yellow",  no_wrap=True,  min_width=8,  justify="right")
    table.add_column("Updated",     style="green",        no_wrap=True,  min_width=14)

    for repo in repos:
        visibility = (
            "[bold red]🔒 Private[/bold red]"
            if repo.get("private")
            else "[bold green]🌐 Public[/bold green]"
        )
        table.add_row(
            repo.get("name", "—"),
            visibility,
            repo.get("language") or "[dim]—[/dim]",
            str(repo.get("stargazers_count", 0)),
            _format_date(repo.get("updated_at", "")),
        )

    console.print(table)
    rprint()