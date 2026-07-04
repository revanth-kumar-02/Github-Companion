from github_companion.services.git_service import get_git_status
from github_companion.services.theme_service import get_active_theme_obj
from rich.panel import Panel
from rich.console import Console
from rich import box

console = Console()

def show_gc_status():
    theme = get_active_theme_obj()
    status = get_git_status()
    
    console.print()
    console.print(f"[bold {theme.header}]Git Repository Status[/bold {theme.header}]")
    console.print("─" * 40, style=theme.border)
    console.print()
    console.print(status.strip() if status.strip() else "Clean working directory, no modifications.")
    console.print()
