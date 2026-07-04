"""Repos command — list the user's GitHub repositories."""
from github_companion.services.github_service import get_github_repositories
from github_companion.services.theme_service import get_active_theme_obj
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


def show_gc_repo():
    """Displays user's repositories in a beautiful Rich Table."""
    theme = get_active_theme_obj()
    repos = get_github_repositories()
    
    rprint()
    rprint(f"[bold {theme.header}]Public Repositories[/bold {theme.header}]")
    rprint(f"[{theme.border}]" + "─" * 47 + f"[/{theme.border}]")
    rprint()
    
    if repos is None:
        rprint("[bold red]Failed to fetch repositories.[/bold red]")
        return
        
    if not repos:
        rprint("[dim]No repositories found.[/dim]")
        return
        
    table = Table(show_header=True, header_style=theme.table_header, border_style=theme.border)
    table.add_column("No.", style=theme.command, justify="right", width=4)
    table.add_column("Repository Name", style="bold white")
    table.add_column("Visibility", style="bold", justify="center")
    table.add_column("Language", style="yellow")
    
    for index, repo in enumerate(repos, start=1):
        visibility = "[bold red]🔒 Private[/bold red]" if repo.get("private") else "[bold green]🌐 Public[/bold green]"
        table.add_row(
            str(index),
            repo.get("name", "—"),
            visibility,
            repo.get("language") or "[dim]—[/dim]"
        )
        
    console.print(table)
    rprint()