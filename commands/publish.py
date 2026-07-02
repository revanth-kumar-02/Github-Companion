"""Publish command — pushes a local project folder to a new GitHub repository."""
import os
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from services.github_service import repo_create
from services.git_service import (
    git_init,
    git_add,
    git_commit,
    git_branch,
    git_remote_add,
    git_push,
)
from services.config_service import get_github_username
from utils.ui import success, error, warning, info

console = Console()


def show_gc_publish():
    rprint()
    rprint("[bold bright_white]Publish Project to GitHub[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    # ── Step 1: Project folder ──────────────────────────────────────────────
    project_path = console.input("[bold cyan]  Project Folder Path : [/bold cyan]").strip()

    if not os.path.isdir(project_path):
        error(f"Folder not found: {project_path}")
        return

    # Auto-detect repo name from folder
    detected_name = os.path.basename(os.path.normpath(project_path))
    repo_name_input = console.input(
        f"[bold cyan]  Repository Name [/bold cyan][dim](Enter to use '{detected_name}')[/dim][bold cyan] : [/bold cyan]"
    ).strip()
    repo_name = repo_name_input if repo_name_input else detected_name

    # ── Step 2: Metadata ────────────────────────────────────────────────────
    description   = console.input("[bold cyan]  Description          : [/bold cyan]").strip()
    private_input = console.input("[bold cyan]  Private? (y/n)        : [/bold cyan]").strip().lower()
    private       = private_input == "y"
    commit_msg    = console.input("[bold cyan]  Commit Message        : [/bold cyan]").strip()

    if not commit_msg:
        commit_msg = "Initial commit"

    rprint()

    # ── Step 3: Create GitHub Repository ───────────────────────────────────
    with console.status("[bold yellow]  Creating GitHub repository...[/bold yellow]"):
        response = repo_create(repo_name, description, private)

    if response.status_code != 201:
        error("Failed to create GitHub repository.")
        err_msg = response.json().get("message", "Unknown error")
        rprint(f"[dim red]  → {err_msg}[/dim red]")
        return

    repo_data   = response.json()
    html_url    = repo_data["html_url"]
    clone_url   = repo_data["clone_url"]
    username    = get_github_username()
    remote_url  = f"https://{username}@github.com/{username}/{repo_name}.git"

    rprint("[bold green]  ✔ GitHub repository created[/bold green]")

    # ── Step 4: Git workflow ────────────────────────────────────────────────
    steps = [
        ("  Initializing Git...",          lambda: git_init(project_path)),
        ("  Staging all files...",         lambda: git_add(project_path)),
        ("  Creating initial commit...",   lambda: git_commit(project_path, commit_msg)),
        ("  Renaming branch to main...",   lambda: git_branch(project_path, "main")),
        ("  Adding remote origin...",      lambda: git_remote_add(project_path, remote_url)),
        ("  Pushing to GitHub...",         lambda: git_push(project_path)),
    ]

    for label, fn in steps:
        with console.status(f"[bold yellow]{label}[/bold yellow]"):
            result = fn()
        rprint(f"[bold green]  ✔[/bold green] {label.strip()}")

    # ── Step 5: Success panel ───────────────────────────────────────────────
    rprint()
    console.print(Panel(
        f"[bold green]🎉 Project published successfully![/bold green]\n\n"
        f"[bold white]Repository :[/bold white] [underline blue]{html_url}[/underline blue]\n"
        f"[bold white]Visibility  :[/bold white] {'🔒 Private' if private else '🌐 Public'}\n"
        f"[bold white]Branch      :[/bold white] main",
        title="[bold green]✅ Publish Complete[/bold green]",
        border_style="green",
        padding=(1, 2),
    ))