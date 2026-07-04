"""Login command — reconfigure GitHub credentials."""
from rich.console import Console
from rich import print as rprint
from github_companion.services.config_service import _load, save_settings
from github_companion.services.setup_wizard import _validate_github_credentials
from github_companion.utils.ui import success, error

console = Console()


def login_cmd() -> None:
    """Prompt user to reconfigure their GitHub credentials."""
    rprint()
    rprint("[bold bright_white]Reconfigure GitHub Credentials[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    username = console.input("[bold cyan]  GitHub Username             : [/bold cyan]").strip()
    token = console.input("[bold cyan]  GitHub Personal Access Token : [/bold cyan]").strip()

    if not username or not token:
        error("Username and Token are required.")
        return

    with console.status("[bold yellow]  Validating credentials...[/bold yellow]", spinner="dots"):
        valid, msg = _validate_github_credentials(username, token)

    if valid:
        settings = _load()
        settings["github_username"] = username
        settings["github_token"] = token
        save_settings(settings)
        success("GitHub credentials updated and saved successfully.")
    else:
        error(f"Validation failed: {msg}")
