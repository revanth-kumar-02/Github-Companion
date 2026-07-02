"""Logout command — remove GitHub credentials."""
from rich.console import Console
from rich import print as rprint
from services.config_service import _load, save_settings
from utils.ui import success

console = Console()


def logout_cmd() -> None:
    """Prompt user to remove GitHub credentials."""
    rprint()
    confirm = console.input("[bold red]Are you sure you want to remove your GitHub credentials? (y/n) : [/bold red]").strip().lower()
    if confirm != "y":
        rprint("[dim]  Cancelled.[/dim]")
        return

    settings = _load()
    settings["github_username"] = ""
    settings["github_token"] = ""
    save_settings(settings)
    success("GitHub credentials removed successfully.")
