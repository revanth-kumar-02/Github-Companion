"""Repos command — list the user's GitHub repositories with standard summary."""
from github_companion.services.github_service import get_github_repositories
from github_companion.services.theme_service import get_active_theme_obj
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


def show_gc_repo():
    """Displays user's repositories in a beautiful Rich Table with summary."""
    theme = get_active_theme_obj()
    
    # 1. Header
    rprint()
    rprint(f"[bold {theme.header}]Public Repositories[/bold {theme.header}]")
    
    # 2. Separator
    rprint(f"[{theme.border}]" + "─" * 47 + f"[/{theme.border}]")
    rprint()
    
    # Fetch repositories (does not print anything)
    repos = get_github_repositories()
    
    if repos is None or not isinstance(repos, list):
        rprint("[bold red]Failed to fetch repositories.[/bold red]")
        rprint()
        return
        
    if not repos:
        rprint("[dim]No repositories found.[/dim]")
        rprint()
        # Print summary with zero values
        rprint(f"[bold {theme.highlight}]Repository Summary[/bold {theme.highlight}]")
        rprint("  Total Repositories : 0")
        rprint("  Public             : 0")
        rprint("  Private            : 0")
        rprint()
        return
        
    # 3. Repository Data Table
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
    
    # 4. Repository Summary
    total = len(repos)
    public_count = sum(1 for r in repos if not r.get("private"))
    private_count = sum(1 for r in repos if r.get("private"))
    
    rprint(f"[bold {theme.highlight}]Repository Summary[/bold {theme.highlight}]")
    rprint(f"  Total Repositories : {total}")
    rprint(f"  Public             : {public_count}")
    rprint(f"  Private            : {private_count}")
    rprint()