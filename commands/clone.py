"""Clone repository command — clone remote GitHub repositories to local workspace."""
import os
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from services.github_service import fetch_repositories
from services.config_service import get_default_workspace
from services.theme_service import get_theme_styles
from services.git_service import git_clone
from utils.ui import success, error, info, warning

console = Console()


def clone_repo() -> None:
    """Interactively list remote repositories and clone them to the local workspace."""
    rprint()
    rprint("[bold bright_white]Retrieve GitHub Repositories[/bold bright_white]")
    rprint("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")

    with console.status("[bold cyan]Fetching repositories from GitHub...[/bold cyan]"):
        try:
            repos = fetch_repositories(limit=50)
        except Exception as e:
            error(f"Failed to fetch repositories: {e}")
            return

    if not repos:
        error("No repositories found or unauthorized. Please verify authentication credentials.")
        return

    # Fetch active theme styling
    theme = get_theme_styles()
    header_style = theme["header_style"]
    border_style = theme["border_style"]
    cat_styles = theme["category_styles"]
    repo_color = cat_styles.get("Repository", "bold hot_pink")

    # Render repositories table
    table = Table(
        show_header=True,
        header_style=header_style,
        border_style=border_style,
        padding=(0, 1),
        expand=False,
    )
    table.add_column("No.", no_wrap=True, style="bold cyan")
    table.add_column("Repository Name", no_wrap=True, style=repo_color)
    table.add_column("Visibility", no_wrap=True)
    table.add_column("Description", no_wrap=False, width=45)

    for idx, repo in enumerate(repos, start=1):
        visibility = "Private" if repo.get("private") else "Public"
        vis_styled = f"[bold red]Private[/bold red]" if repo.get("private") else "[bold green]Public[/bold green]"
        desc = repo.get("description") or ""
        table.add_row(str(idx), repo["name"], vis_styled, desc)

    console.print(table)
    rprint()

    # Select repository
    try:
        selection = console.input("[bold yellow]Select repository to clone (enter number) : [/bold yellow]").strip()
    except (KeyboardInterrupt, EOFError):
        rprint("\n[dim]  Cancelled.[/dim]")
        return

    if not selection:
        rprint("[dim]  Cancelled.[/dim]")
        return

    if not selection.isdigit() or not (1 <= int(selection) <= len(repos)):
        error(f"Invalid selection: '{selection}'")
        return

    selected_repo = repos[int(selection) - 1]
    repo_name = selected_repo["name"]
    clone_url = selected_repo.get("clone_url")

    if not clone_url:
        error("Unable to retrieve clone URL for this repository.")
        return

    # Determine default clone destination folder
    default_ws = get_default_workspace()
    if not default_ws:
        # Fallback to current working directory
        default_ws = os.getcwd()

    default_dest = os.path.join(default_ws, repo_name)
    rprint(f"\nDefault destination: [bold cyan]{default_dest}[/bold cyan]")
    
    try:
        dest_input = console.input(f"[bold yellow]Press Enter to accept, or enter custom path : [/bold yellow]").strip()
    except (KeyboardInterrupt, EOFError):
        rprint("\n[dim]  Cancelled.[/dim]")
        return

    dest_path = dest_input if dest_input else default_dest
    dest_path = os.path.abspath(os.path.expanduser(dest_path))

    # Verify if destination path exists and is not empty
    if os.path.exists(dest_path) and os.listdir(dest_path):
        warning(f"Destination path '{dest_path}' already exists and is not empty.")
        try:
            confirm = console.input("[bold red]Do you still want to proceed? (y/n) : [/bold red]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            rprint("\n[dim]  Cancelled.[/dim]")
            return
        if confirm != "y":
            rprint("[dim]  Cancelled.[/dim]")
            return

    # Clone the repository
    info(f"Cloning '{repo_name}' into '{dest_path}'...")
    rprint(f"[dim]Command: git clone {clone_url} {dest_path}[/dim]")
    
    try:
        result = git_clone(clone_url, dest_path)
        if result.returncode == 0:
            success(f"Successfully cloned '{repo_name}'!")
            rprint(f"[bold cyan]📂 Local Directory :[/bold cyan] [underline blue]{dest_path}[/underline blue]")
        else:
            error(f"Git clone failed:\n{result.stderr}")
    except Exception as e:
        error(f"An unexpected error occurred during cloning: {e}")
