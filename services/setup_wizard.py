"""First-run setup wizard for GitHub Companion."""
import json
import os
from pathlib import Path
import requests
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from services.config_service import CONFIG_PATH, save_settings, ensure_gc_directories

console = Console()


def run_setup_wizard() -> bool:
    """
    Run the interactive first-run setup wizard.
    Returns True if successfully configured and saved, False otherwise.
    """
    rprint()
    console.print(Panel(
        "[bold purple]Welcome to GitHub Companion 🚀[/bold purple]\n\n"
        "It looks like this is your first time using GitHub Companion.\n"
        "Let's configure your development environment.",
        title="[bold purple]Setup Wizard[/bold purple]",
        border_style="purple",
        padding=(1, 2),
    ))
    rprint()
    console.input("[bold yellow]Press Enter to continue...[/bold yellow]")

    # ── STEP 1 & 2: GitHub Configuration ───────────────────────────────────────
    github_username = ""
    github_token = ""
    while True:
        rprint()
        rprint("[bold cyan]STEP 1: GitHub Configuration[/bold cyan]")
        rprint("[dim]───────────────────────────────────────────────[/dim]")
        github_username = console.input("[bold white]  GitHub Username             : [/bold white]").strip()
        # Input password hides typing automatically
        github_token = console.input("[bold white]  GitHub Personal Access Token : [/bold white]").strip()

        if not github_username or not github_token:
            rprint("[bold red]❌ Username and Token are required.[/bold red]")
            continue

        # ── STEP 3: Validate Credentials ──────────────────────────────────────
        with console.status("[bold yellow]  Validating GitHub credentials...[/bold yellow]", spinner="dots"):
            valid, msg = _validate_github_credentials(github_username, github_token)

        if valid:
            rprint("[bold green]  ✓ GitHub Username exists[/bold green]")
            rprint("[bold green]  ✓ GitHub Personal Access Token is valid[/bold green]")
            rprint("[bold green]  ✓ GitHub API is reachable[/bold green]")
            break
        else:
            rprint(f"[bold red]  ❌ Validation failed: {msg}[/bold red]")
            retry = console.input("[bold yellow]Would you like to try again? (y/n) : [/bold yellow]").strip().lower()
            if retry != "y":
                return False

    # ── STEP 4: AI Configuration ───────────────────────────────────────────────
    rprint()
    rprint("[bold cyan]STEP 4: AI Configuration[/bold cyan]")
    rprint("[dim]───────────────────────────────────────────────[/dim]")
    rprint("  Choose an AI Provider:")
    rprint("    [bold cyan]1[/bold cyan]. Ollama (Recommended) [dim]- Local, Offline, Free[/dim]")
    rprint("    [bold cyan]2[/bold cyan]. OpenRouter           [dim]- Cloud AI models[/dim]")
    rprint("    [bold cyan]3[/bold cyan]. Skip for Now")
    rprint()

    provider = "ollama"
    openrouter_key = ""
    ollama_host = "http://localhost:11434"

    while True:
        choice = console.input("[bold yellow]Select option (1/2/3) : [/bold yellow]").strip()
        if choice == "1":
            provider = "ollama"
            # Detect Ollama
            with console.status("[bold yellow]  Detecting local Ollama...[/bold yellow]", spinner="dots"):
                ollama_detected = _detect_ollama(ollama_host)
            if ollama_detected:
                rprint("[bold green]  ✓ Ollama Detected[/bold green]")
            else:
                rprint("[bold yellow]  ⚠️ Ollama is not running or not installed.[/bold yellow]")
                rprint("[dim]  You can download and run it later from https://ollama.com[/dim]")
            break
        elif choice == "2":
            provider = "openrouter"
            while True:
                openrouter_key = console.input("[bold white]  OpenRouter API Key : [/bold white]").strip()
                if not openrouter_key:
                    rprint("[bold red]❌ API Key is required for OpenRouter.[/bold red]")
                    continue
                with console.status("[bold yellow]  Validating OpenRouter key...[/bold yellow]", spinner="dots"):
                    valid_key = _validate_openrouter_key(openrouter_key)
                if valid_key:
                    rprint("[bold green]  ✓ OpenRouter API Key is valid[/bold green]")
                    break
                else:
                    rprint("[bold red]  ❌ Invalid OpenRouter API Key.[/bold red]")
                    retry_key = console.input("[bold yellow]Try key again? (y/n) : [/bold yellow]").strip().lower()
                    if retry_key != "y":
                        provider = "ollama"  # Fallback
                        break
            break
        elif choice == "3":
            provider = "ollama"  # Default skip setting
            rprint("[dim]  Skipping AI setup. Defaulting to Ollama configuration.[/dim]")
            break
        else:
            rprint("[bold red]❌ Invalid choice.[/bold red]")

    # ── STEP 5: Default AI Model ───────────────────────────────────────────────
    coding_model = "qwen2.5-coder"
    reasoning_model = "deepseek-r1"
    assistant_model = "llama3.3"

    if provider == "ollama":
        rprint()
        rprint("[bold cyan]STEP 5: Default AI Model[/bold cyan]")
        rprint("[dim]───────────────────────────────────────────────[/dim]")
        rprint("  Choose Default Coding Model:")
        rprint("    [bold cyan]1[/bold cyan]. Qwen 2.5 Coder ⭐ [dim]Recommended[/dim]")
        rprint("    [bold cyan]2[/bold cyan]. DeepSeek R1")
        rprint("    [bold cyan]3[/bold cyan]. Llama 3.3")
        rprint()
        model_choice = console.input("[bold yellow]Select model (1/2/3) : [/bold yellow]").strip()
        if model_choice == "2":
            coding_model = "deepseek-r1"
        elif model_choice == "3":
            coding_model = "llama3.3"
    else:
        # OpenRouter default assignments
        coding_model = "qwen2.5-coder"
        reasoning_model = "deepseek-r1"
        assistant_model = "deepseek-v3"

    # ── STEP 6: Configuration Summary ──────────────────────────────────────────
    rprint()
    summary = (
        f"[bold yellow]GitHub Configuration[/bold yellow]\n"
        f"  Username       : {github_username}\n\n"
        f"[bold yellow]AI Configuration[/bold yellow]\n"
        f"  AI Provider    : {provider.capitalize()}\n"
        f"  Coding Model   : {coding_model}\n"
        f"  Reasoning Model: {reasoning_model}\n"
        f"  Assistant Model: {assistant_model}\n\n"
        f"[bold yellow]File Location[/bold yellow]\n"
        f"  Configuration  : {CONFIG_PATH}"
    )

    console.print(Panel(
        summary,
        title="[bold green]📋 Configuration Summary[/bold green]",
        border_style="green",
        expand=False,
    ))
    rprint()

    save_choice = console.input("[bold yellow]Save configuration? (y/n) : [/bold yellow]").strip().lower()
    if save_choice != "y":
        rprint("[bold red]❌ Configuration cancelled.[/bold red]")
        return False

    # ── Save settings ──────────────────────────────────────────────────────────
    settings = {
        "github_username": github_username,
        "github_token": github_token,
        "provider": provider,
        "fallback_provider": "openrouter",
        "coding_model": coding_model,
        "reasoning_model": reasoning_model,
        "assistant_model": assistant_model,
        "ollama_host": ollama_host,
    }
    if openrouter_key:
        settings["openrouter_api_key"] = openrouter_key

    try:
        ensure_gc_directories()
        save_settings(settings)
        rprint("\n[bold green]✓ Configuration Saved[/bold green]")
        rprint("[bold green]✓ GitHub Companion is Ready[/bold green]")
        rprint("[bold purple]Happy Coding 🚀[/bold purple]\n")
        return True
    except Exception as e:
        rprint(f"[bold red]❌ Failed to save configuration: {e}[/bold red]")
        return False


def _validate_github_credentials(username: str, token: str) -> tuple[bool, str]:
    """Verify username exists, token is valid, and GitHub API is reachable."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        resp = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            login = data.get("login", "")
            if login.lower() == username.lower():
                return True, "Success"
            else:
                return False, f"Token belongs to user '{login}', not '{username}'."
        elif resp.status_code == 401:
            return False, "Invalid GitHub token (Unauthorized)."
        else:
            return False, f"GitHub API error (Status: {resp.status_code})."
    except Exception as e:
        return False, f"Connection error: {e}"


def _detect_ollama(host: str) -> bool:
    """Return True if Ollama is running locally."""
    try:
        resp = requests.get(f"{host}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def _validate_openrouter_key(api_key: str) -> bool:
    """Verify OpenRouter key validity by hitting its models endpoint."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False
