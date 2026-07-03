"""Doctor command — diagnose development environment and configurations."""
import subprocess
import requests
from rich.console import Console
from rich.table import Table
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
    """Run diagnostics on AI pipelines (doctor ai)."""
    rprint()
    rprint("[bold bright_white]AI Diagnostics 🩺[/bold bright_white]")
    rprint("[blue]" + "─" * 47 + "[/blue]")

    settings = _load()
    
    # 1. Ollama
    ollama_host = settings.get("ollama_host", "http://localhost:11434")
    ollama_configured = "Yes"
    ollama_auth = "Not Required"
    ollama_ok = False
    with console.status("[bold yellow]Testing Ollama...[/bold yellow]", spinner="dots"):
        try:
            resp = requests.get(f"{ollama_host}/api/tags", timeout=3)
            ollama_ok = resp.status_code == 200
        except Exception:
            ollama_ok = False
    ollama_status = "[bold green]✓ Connected[/bold green]" if ollama_ok else "[bold red]✗ Offline[/bold red]"

    # 2. OpenRouter
    or_key = settings.get("openrouter_api_key", "")
    or_configured = "Yes" if or_key else "No"
    or_auth = "Present" if or_key else "Missing"
    or_ok = False
    if or_key:
        with console.status("[bold yellow]Testing OpenRouter...[/bold yellow]", spinner="dots"):
            try:
                from services.setup_wizard import _validate_openrouter_key
                or_ok = _validate_openrouter_key(or_key)
            except Exception:
                or_ok = False
    or_status = "[bold green]✓ Connected[/bold green]" if or_ok else ("[bold red]✗ Disconnected[/bold red]" if or_key else "[dim]Not Configured[/dim]")

    # 3. NVIDIA NIM
    nv_key = settings.get("nvidia_api_key", "")
    nv_configured = "Yes" if nv_key else "No"
    nv_auth = "Present" if nv_key else "Missing"
    nv_ok = False
    nv_endpoint_ok = False
    nv_auth_ok = False
    nv_models_ok = False
    nv_chat_ok = False

    if nv_key:
        with console.status("[bold yellow]Testing NVIDIA NIM...[/bold yellow]", spinner="dots"):
            try:
                headers = {
                    "Authorization": f"Bearer {nv_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                # Check models endpoint reachability and authentication
                resp = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers, timeout=10)
                nv_endpoint_ok = (resp.status_code != 404 and resp.status_code != 502)
                if resp.status_code == 200:
                    nv_auth_ok = True
                    nv_models_ok = True
                elif resp.status_code == 401:
                    nv_auth_ok = False
                
                # Chat completions endpoint validation
                payload = {
                    "model": "nvidia/llama-3.1-nemotron-51b-instruct",
                    "messages": [{"role": "user", "content": "Ping"}],
                    "max_tokens": 1
                }
                resp_chat = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
                if resp_chat.status_code == 200:
                    nv_chat_ok = True
                else:
                    # Fallback to public free-tier model meta/llama-3.1-8b-instruct if default model is restricted
                    payload["model"] = "meta/llama-3.1-8b-instruct"
                    resp_chat_fallback = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
                    if resp_chat_fallback.status_code == 200:
                        nv_chat_ok = True
                
                nv_ok = nv_endpoint_ok and nv_auth_ok and nv_models_ok and nv_chat_ok
            except Exception:
                nv_ok = False
    nv_status = "[bold green]✓ Connected[/bold green]" if nv_ok else ("[bold red]✗ Disconnected[/bold red]" if nv_key else "[dim]Not Configured[/dim]")

    # Gather available models from registry count
    from ai.model_registry import MODELS
    ollama_models = len([m for m in MODELS if m["provider"] == "ollama"])
    or_models = len([m for m in MODELS if m["provider"] == "openrouter"])
    nv_models = len([m for m in MODELS if m["provider"] == "nvidia"])

    # Table
    table = Table(show_header=True, header_style="bold yellow", border_style="purple")
    table.add_column("Provider", style="bold cyan")
    table.add_column("Configured", style="white")
    table.add_column("Authentication", style="white")
    table.add_column("Available Models", style="magenta")
    table.add_column("Connection Status", style="white")

    table.add_row("Ollama", ollama_configured, ollama_auth, str(ollama_models), ollama_status)
    table.add_row("OpenRouter", or_configured, or_auth, str(or_models), or_status)
    table.add_row("NVIDIA NIM", nv_configured, nv_auth, str(nv_models), nv_status)

    console.print(table)
    rprint()

    if nv_key:
        rprint("[bold white]NVIDIA NIM Detailed Checks:[/bold white]")
        rprint(f"  {'[green]✓[/green]' if nv_endpoint_ok else '[red]✗[/red]'} Endpoint reachable (https://integrate.api.nvidia.com/v1)")
        rprint(f"  {'[green]✓[/green]' if nv_auth_ok else '[red]✗[/red]'} Authentication (API key validity)")
        rprint(f"  {'[green]✓[/green]' if nv_models_ok else '[red]✗[/red]'} Available models metadata query")
        rprint(f"  {'[green]✓[/green]' if nv_chat_ok else '[red]✗[/red]'} Chat completion endpoint (chat/completions response)")
        rprint()

