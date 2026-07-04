"""Doctor command — diagnose development environment and configurations."""
import requests
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich import print as rprint

from github_companion.services.config_service import (
    get_github_username,
    get_github_token,
    get_ai_provider,
    get_ollama_host,
    _load,
)
from github_companion.services.theme_service import get_active_theme_obj
from github_companion.utils.ui import success, error, info, warning

console = Console()


def doctor_cmd(args: list[str] = None) -> None:
    """Run diagnostic checks on GitHub, Git, internet connection, and AI providers."""
    if args and args[0].lower() == "ai":
        _doctor_ai()
        return

    theme = get_active_theme_obj()
    border_style = theme.border
    header_style = theme.header
    highlight_style = theme.highlight

    rprint()
    rprint(f"[{header_style}]Running System Diagnostics...[/{header_style}]")

    # ── 1. Internet Connection ────────────────────────────────────────────────
    internet_ok = False
    with console.status("[bold yellow]Checking Internet Connection...[/bold yellow]", spinner="dots"):
        try:
            resp = requests.get("https://api.github.com", timeout=5)
            internet_ok = resp.status_code == 200
        except Exception:
            internet_ok = False

    # ── 2. Git Installation ───────────────────────────────────────────────────
    git_ok = False
    git_version = "Unknown"
    with console.status("[bold yellow]Checking Git Installation...[/bold yellow]", spinner="dots"):
        try:
            from github_companion.services.git_service import get_git_version
            version = get_git_version()
            if version:
                git_ok = True
                git_version = version.strip()
        except Exception:
            git_ok = False

    # ── 3. GitHub Configuration & Token ────────────────────────────────────────
    username = get_github_username()
    token = get_github_token()
    github_ok = False
    github_details = ""

    if not username:
        github_details += "❌ GitHub Username: Not configured\n"
    else:
        github_details += f"ℹ️  GitHub Username: '{username}'\n"

    if not token:
        github_details += "❌ GitHub Token: Not configured\n"
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
                        github_details += "✅ GitHub Token: Valid & matches username\n"
                    else:
                        github_details += f"⚠️  GitHub Token: Token belongs to '{login}', not '{username}'\n"
                elif resp.status_code == 401:
                    github_details += "❌ GitHub Token: Unauthorized / Invalid token\n"
                else:
                    github_details += f"❌ GitHub Token: Verification failed with status {resp.status_code}\n"
            except Exception as e:
                github_details += f"❌ GitHub Token: Verification failed: {e}\n"

    # ── 4. AI Provider Diagnostics ─────────────────────────────────────────────
    settings = _load()
    provider = get_ai_provider()
    provider_details = f"Configured AI Provider: '{provider}'\n"

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
        provider_details += f"✅ Ollama Service: Running at {ollama_host}\n"
    else:
        if provider == "ollama":
            provider_details += f"❌ Ollama Service: Unreachable at {ollama_host} (Ollama serve may not be running)\n"
        else:
            provider_details += f"⚠️  Ollama Service: Offline at {ollama_host}\n"

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
            provider_details += "✅ OpenRouter Config: Valid API Key & Reachable\n"
        else:
            provider_details += "❌ OpenRouter Config: Invalid API Key or Unreachable\n"
    else:
        if provider == "openrouter":
            provider_details += "❌ OpenRouter Config: API Key not set\n"
        else:
            provider_details += "ℹ️  OpenRouter Config: API Key not set\n"

    # Build the Diagnostic Panel
    table = Table.grid(expand=True, padding=(0, 2))
    table.add_column(style=f"bold {highlight_style}", width=25)
    table.add_column(style="white")

    table.add_row("Internet Status:", "✅ Online / Reachable" if internet_ok else "❌ Offline / Unreachable")
    table.add_row("Git Installation:", f"✅ {git_version}" if git_ok else "❌ Not found in PATH")
    table.add_row("GitHub Auth:", github_details.strip())
    table.add_row("AI Provider Config:", provider_details.strip())

    if internet_ok and git_ok and github_ok and (ollama_ok or provider != "ollama"):
        summary_msg = f"[bold green]🎉 Diagnostics clean! GitHub Companion is ready.[/bold green]"
    else:
        summary_msg = f"[bold yellow]⚠️ Diagnostics found issues. Some features may be offline.[/bold yellow]"

    main_table = Table.grid(expand=True)
    main_table.add_row(table)
    main_table.add_row(rprint)  # empty row
    main_table.add_row(summary_msg)

    panel = Panel(
        main_table,
        border_style=border_style,
        box=box.ROUNDED,
        title=f"[{header_style}] 🩺 Environment Diagnostics [/{header_style}]",
        expand=False
    )
    console.print(panel)
    rprint()


def _doctor_ai() -> None:
    """Run diagnostics on AI pipelines (doctor ai)."""
    theme = get_active_theme_obj()
    border_style = theme.border
    header_style = theme.header
    highlight_style = theme.highlight

    rprint()
    rprint(f"[{header_style}]Running AI Pipeline Diagnostics...[/{header_style}]")

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
                from github_companion.services.setup_wizard import _validate_openrouter_key
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
                resp = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers, timeout=10)
                nv_endpoint_ok = (resp.status_code != 404 and resp.status_code != 502)
                if resp.status_code == 200:
                    nv_auth_ok = True
                    nv_models_ok = True
                elif resp.status_code == 401:
                    nv_auth_ok = False
                
                payload = {
                    "model": "nvidia/llama-3.1-nemotron-51b-instruct",
                    "messages": [{"role": "user", "content": "Ping"}],
                    "max_tokens": 1
                }
                resp_chat = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
                if resp_chat.status_code == 200:
                    nv_chat_ok = True
                else:
                    payload["model"] = "meta/llama-3.1-8b-instruct"
                    resp_chat_fallback = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
                    if resp_chat_fallback.status_code == 200:
                        nv_chat_ok = True
                
                nv_ok = nv_endpoint_ok and nv_auth_ok and nv_models_ok and nv_chat_ok
            except Exception:
                nv_ok = False
    nv_status = "[bold green]✓ Connected[/bold green]" if nv_ok else ("[bold red]✗ Disconnected[/bold red]" if nv_key else "[dim]Not Configured[/dim]")

    # Gather available models from registry count
    from github_companion.ai.model_registry import MODELS
    ollama_models = len([m for m in MODELS if m["provider"] == "ollama"])
    or_models = len([m for m in MODELS if m["provider"] == "openrouter"])
    nv_models = len([m for m in MODELS if m["provider"] == "nvidia"])

    # Table
    table = Table(show_header=True, header_style=theme.table_header, border_style=border_style)
    table.add_column("Provider", style=theme.command)
    table.add_column("Configured", style="white")
    table.add_column("Authentication", style="white")
    table.add_column("Available Models", style=highlight_style)
    table.add_column("Connection Status", style="white")

    table.add_row("Ollama", ollama_configured, ollama_auth, str(ollama_models), ollama_status)
    table.add_row("OpenRouter", or_configured, or_auth, str(or_models), or_status)
    table.add_row("NVIDIA NIM", nv_configured, nv_auth, str(nv_models), nv_status)

    panel = Panel(
        table,
        border_style=border_style,
        box=box.ROUNDED,
        title=f"[{header_style}] 🩺 AI Provider Connection Diagnostics [/{header_style}]",
        expand=False
    )
    console.print(panel)
    rprint()

    if nv_key:
        nv_checks = []
        nv_checks.append(f"  {'[green]✓[/green]' if nv_endpoint_ok else '[red]✗[/red]'} Endpoint reachable (integrate.api.nvidia.com)")
        nv_checks.append(f"  {'[green]✓[/green]' if nv_auth_ok else '[red]✗[/red]'} Authentication validation (API key check)")
        nv_checks.append(f"  {'[green]✓[/green]' if nv_models_ok else '[red]✗[/red]'} NIM metadata registry query")
        nv_checks.append(f"  {'[green]✓[/green]' if nv_chat_ok else '[red]✗[/red]'} NIM chat engine test completions")
        
        console.print(Panel(
            "\n".join(nv_checks),
            title="[bold purple]NVIDIA NIM Detailed Checks[/bold purple]",
            border_style=border_style,
            expand=False
        ))
        rprint()
