"""Publish command — pushes a local project folder to a new GitHub repository with secure defaults and confirmations."""
import os
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from github_companion.services.github_service import repo_create
from github_companion.services.git_service import (
    git_init,
    git_add,
    git_commit,
    git_branch,
    git_remote_add,
    git_push,
)
from github_companion.services.config_service import get_github_username
from github_companion.utils.ui import success, error, warning, info
from github_companion.utils.security import (
    validate_safe_path,
    prompt_confirmation,
    SecurityError,
)

console = Console()


def show_gc_publish() -> None:
    rprint()
    rprint("[bold bright_white]Publish Project to GitHub[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    # ── Step 1: Project folder ──────────────────────────────────────────────
    raw_path = console.input("[bold cyan]  Project Folder Path : [/bold cyan]").strip()
    try:
        safe_path = validate_safe_path(raw_path)
    except (SecurityError, FileNotFoundError) as exc:
        error(f"Invalid project folder: {exc}")
        return

    if not os.path.isdir(safe_path):
        error(f"Folder not found or not a directory: {safe_path}")
        return

    # Auto-detect repo name from folder
    detected_name = os.path.basename(os.path.normpath(safe_path))
    repo_name_input = console.input(
        f"[bold cyan]  Repository Name [/bold cyan][dim](Enter to use '{detected_name}')[/dim][bold cyan] : [/bold cyan]"
    ).strip()
    repo_name = repo_name_input if repo_name_input else detected_name

    # ── Step 2: Metadata & Safe Defaults ────────────────────────────────────
    description = console.input("[bold cyan]  Description          : [/bold cyan]").strip()

    # SEC-04: Default to PRIVATE for safety
    private_input = console.input(
        "[bold cyan]  Private Repository? [/bold cyan][dim]([Y]/n)[/dim][bold cyan] : [/bold cyan]"
    ).strip().lower()
    private = private_input not in ("n", "no", "public", "p")

    commit_msg = console.input("[bold cyan]  Commit Message [/bold cyan][dim](Enter for 'Initial commit')[/dim] : ").strip()
    if not commit_msg:
        commit_msg = "Initial commit"

    visibility_label = "🔒 Private" if private else "🌐 Public"

    # Confirmation before external action
    rprint()
    rprint(f"[bold yellow]Review Publish Settings:[/bold yellow]")
    rprint(f"  Target Path : {safe_path}")
    rprint(f"  Repo Name   : {repo_name}")
    rprint(f"  Visibility  : {visibility_label}")
    rprint(f"  Commit Msg  : {commit_msg}")
    rprint()

    confirm_prompt = f"Proceed with publishing to GitHub? (y/N): "
    if not prompt_confirmation(confirm_prompt):
        rprint("[dim]  Publishing cancelled by user.[/dim]\n")
        return

    rprint()

    # ── Step 3: Create GitHub Repository ───────────────────────────────────
    with console.status("[bold yellow]  Creating GitHub repository...[/bold yellow]"):
        try:
            response = repo_create(repo_name, description, private)
        except Exception as exc:
            error(f"Network error while creating repository: {exc}")
            return

    if response.status_code != 201:
        error("Failed to create GitHub repository.")
        try:
            err_msg = response.json().get("message", "Unknown error")
            rprint(f"[dim red]  → {err_msg}[/dim red]")
        except Exception:
            pass
        return

    repo_data = response.json()
    html_url = repo_data.get("html_url", "")
    username = get_github_username()
    remote_url = f"https://{username}@github.com/{username}/{repo_name}.git"

    rprint("[bold green]  ✔ GitHub repository created[/bold green]")

    # ── Step 4: Git workflow with failure verification ──────────────────────
    project_str = str(safe_path)
    steps = [
        ("  Initializing Git...",        lambda: git_init(project_str)),
        ("  Staging all files...",       lambda: git_add(project_str)),
        ("  Creating initial commit...", lambda: git_commit(project_str, commit_msg)),
        ("  Renaming branch to main...", lambda: git_branch(project_str, "main")),
        ("  Adding remote origin...",    lambda: git_remote_add(project_str, remote_url)),
        ("  Pushing to GitHub...",       lambda: git_push(project_str)),
    ]

    for label, fn in steps:
        with console.status(f"[bold yellow]{label}[/bold yellow]"):
            try:
                res = fn()
            except Exception as exc:
                error(f"Failed during '{label.strip()}': {exc}")
                return
        rprint(f"[bold green]  ✔[/bold green] {label.strip()}")

    # ── Step 5: Success panel ───────────────────────────────────────────────
    rprint()
    console.print(Panel(
        f"[bold green]🎉 Project published successfully![/bold green]\n\n"
        f"[bold white]Repository :[/bold white] [underline blue]{html_url}[/underline blue]\n"
        f"[bold white]Visibility  :[/bold white] {visibility_label}\n"
        f"[bold white]Branch      :[/bold white] main",
        title="[bold green]✅ Publish Complete[/bold green]",
        border_style="green",
        padding=(1, 2),
    ))