from github_companion.services.git_service import get_git_status
from github_companion.services.theme_service import get_active_theme_obj
from rich.panel import Panel
from rich.console import Console
from rich import box

console = Console()

def show_gc_status():
    theme = get_active_theme_obj()
    status = get_git_status()
    
    panel = Panel(
        status.strip() if status.strip() else "Clean working directory, no modifications.",
        title=f"[bold {theme.header}] Git Repository Status [/bold {theme.header}]",
        border_style=theme.border,
        box=box.ROUNDED,
        expand=False
    )
    console.print()
    console.print(panel)
    console.print()
