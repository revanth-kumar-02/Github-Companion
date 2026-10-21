"""Delete command — securely delete a GitHub repository with explicit name confirmation."""
from rich.console import Console
from rich import print as rprint
from github_companion.services.github_service import repo_delete
from github_companion.utils.ui import success, error
from github_companion.utils.security import prompt_confirmation

console = Console()


def delete_repo() -> None:
    """Prompt for repository name and require typing the exact name to confirm deletion."""
    rprint()
    rprint("[bold bright_white]Delete Remote Repository[/bold bright_white]")
    rprint("[red]" + "─" * 47 + "[/red]")

    repo_name = console.input("[bold cyan]  Repository Name to Delete : [/bold cyan]").strip()
    if not repo_name:
        error("Repository name cannot be empty.")
        return

    rprint(f"\n[bold red]⚠️  WARNING: This will permanently delete '{repo_name}' from GitHub.[/bold red]")
    confirm_prompt = f"  To confirm deletion, type '{repo_name}': "

    confirmed = prompt_confirmation(confirm_prompt, expected_match=repo_name)
    if not confirmed:
        rprint("[dim]  Deletion cancelled. Name did not match or request was aborted.[/dim]\n")
        return

    with console.status(f"[bold yellow]  Deleting repository '{repo_name}'...[/bold yellow]"):
        try:
            response = repo_delete(repo_name)
        except Exception as exc:
            error(f"Network error while deleting repository: {exc}")
            return

    if response.status_code == 204:
        success(f"Repository '{repo_name}' deleted successfully.")
    else:
        error("Failed to delete repository.")
        try:
            err_msg = response.json().get("message", "Unknown error")
            rprint(f"[dim red]  Status {response.status_code}: {err_msg}[/dim red]")
        except Exception:
            rprint(f"[dim red]  Status {response.status_code}[/dim red]")
    rprint()