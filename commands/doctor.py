"""Doctor command — diagnose development environment and configurations."""
import subprocess
import requests
from rich.console import Console
from rich import print as rprint

from services.config_service import (
    get_github_username,
    get_github_token,
    get_ai_provider,
    get_ollama_host,
    _load,
)
from utils.ui import success, error, info, warning

console = Console()


def doctor_cmd() -> None:
    """Run diagnostic checks on GitHub, Git, internet connection, and AI providers."""
    rprint()
    rprint("[bold bright_white]GitHub Companion Diagnostic Doctor 🩺[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")
    rprint("[dim]Running system diagnostics...[/dim]\n")

    # ── 1. Internet Connection ────────────────────────────────────────────────
    internet_ok = False
    with console.status("[bold yellow]Checking Internet Connection...[/bold yellow]", spinner="dots"):
        try:
            resp = requests.get("https://api.github.com", timeout=5)
            internet_ok = resp.status_code == 200
        except Exception:
            internet_ok = False

    if internet_ok:
        success("Internet Connection: Reachable")
    else:
        error("Internet Connection: Unreachable or offline")
        warning("Please verify your internet connection. Diagnostic checks may fail.")

    # ── 2. Git Installation ───────────────────────────────────────────────────
    git_ok = False
    git_version = "Unknown"
    with console.status("[bold yellow]Checking Git Installation...[/bold yellow]", spinner="dots"):
        try:
            res = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                git_ok = True
                git_version = res.stdout.strip()
        except Exception:
            git_ok = False

    if git_ok:
        success(f"Git Installed: {git_version}")
    else:
        error("Git Installed: Not found in PATH. Please install Git.")

    # ── 3. GitHub Configuration & Token ────────────────────────────────────────
    username = get_github_username()
    token = get_github_token()
    github_ok = False

    if not username:
        error("GitHub Username: Not configured")
    else:
        info(f"GitHub Username: '{username}'")

    if not token:
        error("GitHub Token: Not configured")
    else:
        with console.status("[bold yellow]Validating GitHub Token...[/bold yellow]", spinner="dots"):
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
                        github_ok = True
                        success("GitHub Token: Valid & matches configured username")
                    else:
                        warning(f"GitHub Token: Token belongs to '{login}', not '{username}'")
                elif resp.status_code == 401:
                    error("GitHub Token: Unauthorized / Invalid token")
                else:
                    error(f"GitHub Token: Verification request returned status code {resp.status_code}")
            except Exception as e:
                error(f"GitHub Token: Verification request failed: {e}")

    # ── 4. AI Provider Diagnostics ─────────────────────────────────────────────
    settings = _load()
    provider = get_ai_provider()
    info(f"Configured AI Provider: '{provider}'")

    # Ollama check
    ollama_host = get_ollama_host()
    ollama_ok = False
    with console.status("[bold yellow]Checking Ollama status...[/bold yellow]", spinner="dots"):
        try:
            resp = requests.get(f"{ollama_host}/api/tags", timeout=3)
            ollama_ok = resp.status_code == 200
        except Exception:
            ollama_ok = False

    if ollama_ok:
        success(f"Ollama Service: Running at {ollama_host}")
    else:
        if provider == "ollama":
            error(f"Ollama Service: Unreachable at {ollama_host}")
            info("Please start Ollama locally using 'ollama serve'")
        else:
            warning(f"Ollama Service: Offline at {ollama_host}")

    # OpenRouter check
    or_key = settings.get("openrouter_api_key", "")
    if or_key and or_key not in ("YOUR_OPENROUTER_KEY_HERE", "YOUR_KEY"):
        or_ok = False
        with console.status("[bold yellow]Checking OpenRouter status...[/bold yellow]", spinner="dots"):
            try:
                headers = {"Authorization": f"Bearer {or_key}"}
                resp = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=5)
                or_ok = resp.status_code == 200
            except Exception:
                or_ok = False
        if or_ok:
            success("OpenRouter Config: Valid API Key & Reachable")
        else:
            error("OpenRouter Config: Invalid API Key or Unreachable")
    else:
        if provider == "openrouter":
            error("OpenRouter Config: API Key not set")
        else:
            info("OpenRouter Config: API Key not set (Ollama is primary)")

    # Summary
    rprint()
    if internet_ok and git_ok and github_ok and (ollama_ok or provider != "ollama"):
        rprint("[bold green]  🎉 Diagnostics clean! GitHub Companion is ready to go.[/bold green]")
    else:
        rprint("[bold yellow]  ⚠️ Diagnostics found issues. Some features might not work correctly.[/bold yellow]")
    rprint()
