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


def doctor_cmd(args: list[str] = None) -> None:
    """Run diagnostic checks on GitHub, Git, internet connection, and AI providers."""
    if args and args[0].lower() == "ai":
        _doctor_ai()
        return

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


def _doctor_ai() -> None:
    """Run diagnostics on AI OpenRouter authentication pipeline (doctor ai)."""
    rprint()
    rprint("[bold bright_white]AI Authentication Diagnostics 🩺[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    settings = _load()
    provider = settings.get("provider", "ollama")
    rprint(f"  [bold white]Provider[/bold white]              : {provider.capitalize()}")

    # 1. API Key check
    key = settings.get("openrouter_api_key", "")
    has_key = bool(key and key not in ("YOUR_OPENROUTER_KEY_HERE", "YOUR_KEY"))
    if has_key:
        rprint("  [bold white]API Key[/bold white]               : [green]Loaded ✓[/green]")
    else:
        rprint("  [bold white]API Key[/bold white]               : [red]Loaded ✗[/red]")
        rprint("\n[bold red]Stage Failed: API Key not loaded[/bold red]")
        rprint("Please run 'config ai' or 'auth' to set your OpenRouter API key.")
        return

    # 2. Configuration check
    try:
        valid_cfg = "provider" in settings
        if valid_cfg:
            rprint("  [bold white]Configuration[/bold white]         : [green]Valid ✓[/green]")
        else:
            raise ValueError("Missing provider key")
    except Exception as e:
        rprint(f"  [bold white]Configuration[/bold white]         : [red]Valid ✗ ({e})[/red]")
        rprint("\n[bold red]Stage Failed: Configuration check[/bold red]")
        return

    # 3. Authorization Header check
    auth_header = f"Bearer {key}"
    has_bearer = auth_header.startswith("Bearer ") and len(auth_header.split()) == 2
    if has_bearer:
        rprint("  [bold white]Authorization Header[/bold white]  : [green]Present ✓[/green]")
    else:
        rprint("  [bold white]Authorization Header[/bold white]  : [red]Present ✗[/red]")
        rprint("\n[bold red]Stage Failed: Authorization Header malformed[/bold red]")
        return

    # 4. Endpoint check
    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    try:
        resp = requests.options(endpoint, timeout=5)
        rprint("  [bold white]Endpoint[/bold white]              : [green]Valid ✓[/green]")
    except Exception as e:
        rprint(f"  [bold white]Endpoint[/bold white]              : [red]Valid ✗ ({e})[/red]")
        rprint("\n[bold red]Stage Failed: Endpoint connection failed[/bold red]")
        return

    # 5. Test Request
    try:
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/revanth-kumar-02/Github-Companion",
            "X-Title": "GitHub Companion"
        }
        payload = {
            "model": "qwen/qwen2.5-coder-32b-instruct",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        if resp.status_code == 200:
            rprint("  [bold white]Test Request[/bold white]          : [green]Passed ✓[/green]")
        else:
            rprint(f"  [bold white]Test Request[/bold white]          : [red]Passed ✗ (HTTP {resp.status_code})[/red]")
            if resp.status_code == 401:
                rprint("\n[bold red]Stage Failed: Test Request (Unauthorized)[/bold red]")
                rprint("Your OpenRouter API Key appears to be invalid or expired.")
            else:
                err_msg = resp.json().get('error', {}).get('message', 'Unknown error')
                rprint(f"\n[bold red]Stage Failed: Test Request ({err_msg})[/bold red]")
            return
    except Exception as e:
        rprint(f"  [bold white]Test Request[/bold white]          : [red]Passed ✗ ({e})[/red]")
        rprint("\n[bold red]Stage Failed: Test Request connection failure[/bold red]")
        return

    rprint("\n[bold green]  🎉 OpenRouter AI Pipeline is fully functional! [/bold green]\n")

