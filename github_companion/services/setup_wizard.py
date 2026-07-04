"""First-run setup wizard for GitHub Companion with redesigned Rich UI."""
import json
import os
import sys
from pathlib import Path
import requests

from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.rule import Rule
from rich.text import Text
from rich import print as rprint

from github_companion.services.config_service import CONFIG_PATH, save_settings, ensure_gc_directories

console = Console()


def get_masked_input(prompt: str) -> str:
    """
    Read character input while masking it with '*' stars.
    Cross-platform (Windows & Unix tty), copy-paste friendly.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()

    if os.name == "nt":
        import msvcrt
        password = []
        while True:
            ch_bytes = msvcrt.getch()
            # Handle special or extended key sequences (arrow keys etc.)
            if ch_bytes in (b'\x00', b'\xe0'):
                if msvcrt.kbhit():
                    msvcrt.getch()
                continue
                
            try:
                ch = ch_bytes.decode("utf-8", errors="ignore")
            except Exception:
                continue

            # Ctrl+C
            if ch == "\x03":
                raise KeyboardInterrupt()

            # Enter
            if ch in ("\r", "\n"):
                sys.stdout.write("\n")
                sys.stdout.flush()
                break

            # Backspace
            elif ch in ("\b", "\x08"):
                if len(password) > 0:
                    password.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            else:
                # Standard printable ASCII characters
                if ch_bytes[0] >= 32 and ch_bytes[0] != 224:
                    password.append(ch)
                    sys.stdout.write("*")
                    sys.stdout.flush()
        return "".join(password)
    else:
        try:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            password = []
            try:
                tty.setraw(fd)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        sys.stdout.write("\n\r")
                        sys.stdout.flush()
                        break
                    elif ch in ("\x7f", "\x08"):
                        if len(password) > 0:
                            password.pop()
                            sys.stdout.write("\b \b")
                            sys.stdout.flush()
                    elif ch == "\x03":
                        raise KeyboardInterrupt()
                    else:
                        password.append(ch)
                        sys.stdout.write("*")
                        sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return "".join(password).strip()
        except ImportError:
            # Fallback to getpass if tty/termios is unavailable
            import getpass
            res = getpass.getpass("")
            sys.stdout.write("*" * len(res) + "\n")
            sys.stdout.flush()
            return res


def print_step_header(step: int, total_steps: int, title: str) -> None:
    """Clear terminal and render a standard step header using Rich components."""
    console.clear()
    rprint()
    console.print(Rule(title="[bold purple]GitHub Companion Setup[/bold purple]", style="purple"))
    
    progress_bar = "■" * step + "□" * (total_steps - step)
    header_text = Text()
    header_text.append(f"Step {step} of {total_steps}  |  ", style="bold white")
    header_text.append(progress_bar, style="magenta")
    header_text.append(f"\n{title}\n", style="bold cyan")
    
    console.print(Align.center(header_text))
    console.print(Rule(style="purple"))
    rprint()


def run_setup_wizard() -> bool:
    """Run the interactive setup wizard."""
    from github_companion.services.theme_service import get_available_themes, set_active_theme
    
    # ── Welcome Screen ─────────────────────────────────────────────────────────
    console.clear()
    rprint()
    
    welcome_text = Text()
    welcome_text.append("GitHub Companion 🚀\n\n", style="bold purple")
    welcome_text.append("First Time Setup\n\n", style="bold white")
    welcome_text.append("Welcome to GitHub Companion.\n", style="white")
    welcome_text.append("Let's configure your development\n", style="white")
    welcome_text.append("environment before getting started.", style="white")
    
    panel = Panel(
        Align.center(welcome_text),
        border_style="purple",
        expand=False,
        padding=(1, 4)
    )
    console.print(Align.center(panel))
    rprint()
    console.input("[bold yellow]Press Enter to continue...[/bold yellow]")

    # ── STEP 1: GitHub Configuration ───────────────────────────────────────────
    github_username = ""
    github_token = ""
    
    while True:
        print_step_header(1, 5, "GitHub Configuration")
        
        rprint("[bold white]GitHub Username[/bold white]")
        github_username = console.input("[bold purple]> [/bold purple]").strip()
        
        rprint("\n[bold white]GitHub Personal Access Token[/bold white]")
        github_token = get_masked_input("> ")
        
        if not github_username or not github_token:
            rprint("\n[bold red]❌ Username and Token are required.[/bold red]")
            console.input("\nPress Enter to try again...")
            continue

        with console.status("[bold yellow]Validating GitHub credentials...[/bold yellow]", spinner="dots"):
            valid, msg = _validate_github_credentials(github_username, github_token)

        if valid:
            rprint("\n[bold green]✓ Credentials validated successfully.[/bold green]")
            console.input("\nPress Enter to continue...")
            break
        else:
            rprint(f"\n[bold red]❌ Validation failed: {msg}[/bold red]")
            retry = console.input("\n[bold yellow]Would you like to try again? (y/n) : [/bold yellow]").strip().lower()
            if retry != "y":
                return False

    # ── STEP 2: Choose your Workspace Location ─────────────────────────────────
    print_step_header(2, 5, "Choose your Workspace Location")
    home = os.path.expanduser("~")
    default_workspace = os.path.join(home, "GC-Projects")

    rprint(f"Default Location: [cyan]{default_workspace}[/cyan]\n")
    rprint("Press Enter to use default, or enter a custom parent directory path.")
    parent_input = console.input("[bold purple]Location: [/bold purple]").strip()

    if not parent_input:
        workspace_path = default_workspace
    else:
        parent_input = os.path.abspath(os.path.expanduser(parent_input))
        if parent_input.endswith("GC-Projects") or parent_input.endswith("GC-Projects/"):
            workspace_path = parent_input
        else:
            workspace_path = os.path.join(parent_input, "GC-Projects")

    try:
        os.makedirs(workspace_path, exist_ok=True)
        rprint(f"\n[bold green]✓ Workspace configured at: {workspace_path}[/bold green]")
    except Exception as e:
        rprint(f"\n[bold red]❌ Failed to create directory: {e}. Using default instead.[/bold red]")
        workspace_path = default_workspace
        os.makedirs(workspace_path, exist_ok=True)

    console.input("\nPress Enter to continue...")

    # ── STEP 3: Visual Theme Selection ─────────────────────────────────────────
    print_step_header(3, 5, "Visual Theme Selection")
    themes = get_available_themes()
    rprint("Choose a visual theme palette for GC:\n")
    for idx, t in enumerate(themes, start=1):
        rprint(f"  [bold cyan][{idx}][/bold cyan] {t.capitalize()}")
    rprint()
    
    selected_theme = "default"
    while True:
        theme_choice = console.input("[bold purple]> [/bold purple]").strip()
        try:
            val = int(theme_choice)
            if 1 <= val <= len(themes):
                selected_theme = themes[val - 1]
                set_active_theme(selected_theme)
                rprint(f"\n[bold green]✓ Theme set to {selected_theme.capitalize()}[/bold green]")
                break
            else:
                rprint(f"[bold red]❌ Invalid choice. Select 1 to {len(themes)}.[/bold red]")
        except ValueError:
            if theme_choice in themes:
                selected_theme = theme_choice
                set_active_theme(selected_theme)
                rprint(f"\n[bold green]✓ Theme set to {selected_theme.capitalize()}[/bold green]")
                break
            rprint(f"[bold red]❌ Invalid choice. Select 1 to {len(themes)}.[/bold red]")
    console.input("\nPress Enter to continue...")

    # ── STEP 4: AI Provider Selection ──────────────────────────────────────────
    provider = "ollama"
    openrouter_key = ""
    nvidia_key = ""
    ollama_host = "http://localhost:11434"
    
    while True:
        print_step_header(4, 5, "AI Provider Selection")
        
        rprint("Choose an AI Provider:\n")
        rprint("  [bold cyan][1][/bold cyan] Ollama (Recommended)")
        rprint("      Offline - No API Key Required\n")
        rprint("  [bold cyan][2][/bold cyan] OpenRouter")
        rprint("      Cloud AI Models\n")
        rprint("  [bold cyan][3][/bold cyan] NVIDIA NIM")
        rprint("      High-performance optimized inference\n")
        rprint("  [bold cyan][4][/bold cyan] Skip for Now\n")
        
        choice = console.input("[bold purple]> [/bold purple]").strip()
        
        if choice == "1":
            provider = "ollama"
            rprint("\n[bold yellow]Detecting local Ollama...[/bold yellow]")
            if _detect_ollama(ollama_host):
                rprint("[bold green]✓ Ollama Detected[/bold green]")
            else:
                rprint("[bold yellow]⚠️ Ollama is not running or not installed.[/bold yellow]")
                rprint("You can download and run it later from https://ollama.com")
            console.input("\nPress Enter to continue...")
            break
            
        elif choice == "2":
            provider = "openrouter"
            key_valid = False
            while not key_valid:
                rprint("\n[bold white]OpenRouter API Key[/bold white]")
                openrouter_key = get_masked_input("> ")
                if not openrouter_key:
                    rprint("[bold red]❌ API Key is required for OpenRouter.[/bold red]")
                    continue
                    
                with console.status("[bold yellow]Validating OpenRouter key...[/bold yellow]", spinner="dots"):
                    valid_key = _validate_openrouter_key(openrouter_key)
                    
                if valid_key:
                    rprint("[bold green]✓ OpenRouter API Key is valid[/bold green]")
                    key_valid = True
                    console.input("\nPress Enter to continue...")
                else:
                    rprint("[bold red]❌ Invalid OpenRouter API Key.[/bold red]")
                    retry_key = console.input("\nTry key again? (y/n) : ").strip().lower()
                    if retry_key != "y":
                        provider = "ollama"  # Fallback to Ollama
                        break
            break

        elif choice == "3":
            provider = "nvidia"
            key_valid = False
            while not key_valid:
                rprint("\n[bold white]NVIDIA API Key[/bold white]")
                nvidia_key = get_masked_input("> ")
                if not nvidia_key:
                    rprint("[bold red]❌ API Key is required for NVIDIA NIM.[/bold red]")
                    continue

                with console.status("[bold yellow]Validating NVIDIA key...[/bold yellow]", spinner="dots"):
                    valid_key = _validate_nvidia_key(nvidia_key)

                if valid_key:
                    rprint("[bold green]✓ NVIDIA API Key is valid[/bold green]")
                    key_valid = True
                    console.input("\nPress Enter to continue...")
                else:
                    rprint("[bold red]❌ Invalid NVIDIA API Key.[/bold red]")
                    retry_key = console.input("\nTry key again? (y/n) : ").strip().lower()
                    if retry_key != "y":
                        provider = "ollama"  # Fallback to Ollama
                        break
            break
            
        elif choice == "4":
            provider = "ollama"
            rprint("\n[dim]AI setup skipped. Defaulting to Ollama.[/dim]")
            console.input("\nPress Enter to continue...")
            break
        else:
            rprint("[bold red]❌ Invalid choice. Select 1, 2, 3, or 4.[/bold red]")
            console.input("\nPress Enter to try again...")

    # ── STEP 5: Default AI Model Selection ─────────────────────────────────────
    coding_model = "qwen2.5-coder"
    reasoning_model = "deepseek-r1"
    assistant_model = "llama3.3"
    
    print_step_header(5, 5, "Default AI Model Selection")
    
    from github_companion.ai.model_registry import get_models_by_provider
    
    prov_models = get_models_by_provider(provider)
    rprint(f"Select your default model for {provider.upper()}:\n")
    for idx, m in enumerate(prov_models, start=1):
        rec_tag = " ⭐ Recommended" if m.get("recommended") else ""
        rprint(f"  [bold cyan][{idx}][/bold cyan] {m['display_name']} ({m['model_id']}){rec_tag}")
    rprint()
    
    while True:
        model_choice = console.input("[bold purple]> [/bold purple]").strip()
        try:
            val = int(model_choice)
            if 1 <= val <= len(prov_models):
                selected = prov_models[val - 1]
                coding_model = selected["model_id"]
                assistant_model = selected["model_id"]
                reasoning_model = selected["model_id"]
                
                # Refine assistant/reasoning from provider defaults
                for m in prov_models:
                    if m["role"] == "assistant" and m.get("recommended"):
                        assistant_model = m["model_id"]
                    if m["role"] == "planning" and m.get("recommended"):
                        reasoning_model = m["model_id"]
                break
            else:
                rprint(f"[bold red]❌ Invalid choice. Select 1 to {len(prov_models)}.[/bold red]")
        except ValueError:
            rprint(f"[bold red]❌ Invalid choice. Select 1 to {len(prov_models)}.[/bold red]")
                
    console.input("\nPress Enter to view configuration summary...")

    # ── Summary Screen ─────────────────────────────────────────────────────────
    console.clear()
    rprint()
    
    summary_text = Text()
    summary_text.append("Configuration Summary\n\n", style="bold yellow")
    summary_text.append(f"GitHub Username : {github_username}\n", style="white")
    summary_text.append(f"AI Provider     : {provider.capitalize()}\n", style="white")
    summary_text.append(f"Coding Model    : {coding_model}\n", style="white")
    summary_text.append(f"Workspace Path  : {workspace_path}\n", style="white")
    summary_text.append(f"Visual Theme    : {selected_theme.capitalize()}\n", style="white")
    summary_text.append(f"Config Location : {CONFIG_PATH}\n", style="dim")
    
    panel_sum = Panel(
        Align.center(summary_text),
        title="[bold green]📋 Setup Summary[/bold green]",
        border_style="green",
        expand=False,
        padding=(1, 4)
    )
    console.print(Align.center(panel_sum))
    rprint()
    
    save_choice = console.input("[bold yellow]Save configuration? (y/n) : [/bold yellow]").strip().lower()
    if save_choice != "y":
        rprint("[bold red]❌ Configuration cancelled.[/bold red]")
        return False

    # ── Save settings ──────────────────────────────────────────────────────────
    settings = _load()
    settings.update({
        "github_username": github_username,
        "github_token": github_token,
        "provider": provider,
        "fallback_provider": "openrouter",
        "coding_model": coding_model,
        "reasoning_model": reasoning_model,
        "assistant_model": assistant_model,
        "ollama_host": ollama_host,
        "workspace": workspace_path,
        "theme": selected_theme,
    })
    if openrouter_key:
        settings["openrouter_api_key"] = openrouter_key
    if nvidia_key:
        settings["nvidia_api_key"] = nvidia_key

    try:
        ensure_gc_directories()
        save_settings(settings)
        
        # Run final environment checks
        rprint("\n[bold yellow]⚡ Running final environment diagnostics check...[/bold yellow]")
        
        internet_ok = False
        try:
            resp = requests.get("https://api.github.com", timeout=3)
            internet_ok = resp.status_code == 200
        except Exception:
            internet_ok = False
            
        git_ok = False
        try:
            from github_companion.services.git_service import get_git_version
            git_ok = bool(get_git_version())
        except Exception:
            git_ok = False
            
        provider_ok = False
        if provider == "ollama":
            try:
                resp = requests.get(f"{ollama_host}/api/tags", timeout=3)
                provider_ok = resp.status_code == 200
            except Exception:
                provider_ok = False
        elif provider == "openrouter":
            try:
                valid_key = _validate_openrouter_key(openrouter_key)
                provider_ok = valid_key
            except Exception:
                provider_ok = False
        elif provider == "nvidia":
            try:
                valid_key = _validate_nvidia_key(nvidia_key)
                provider_ok = valid_key
            except Exception:
                provider_ok = False

        # Success Screen
        console.clear()
        rprint()
        
        from rich import box
        success_text = Text()
        success_text.append("🎉 Setup Complete / Congratulations!\n\n", style="bold green")
        success_text.append("GitHub Companion is configured and verified.\n\n", style="white")
        success_text.append("Environment Diagnostics:\n", style="bold white")
        success_text.append(f"  Internet Connectivity : {'[green]✓ Connected[/green]' if internet_ok else '[red]✗ Offline[/red]'}\n")
        success_text.append(f"  Git CLI Installation  : {'[green]✓ Installed[/green]' if git_ok else '[red]✗ Missing[/red]'}\n")
        success_text.append(f"  AI Provider Endpoints : {'[green]✓ Reachable[/green]' if provider_ok else '[yellow]⚠️ Unreachable[/yellow]'}\n\n")
        success_text.append("Happy Coding 🚀", style="bold purple")
        
        panel_ok = Panel(
            Align.center(success_text),
            border_style="green",
            box=box.ROUNDED,
            expand=False,
            padding=(1, 4)
        )
        console.print(Align.center(panel_ok))
        rprint()
        console.input("[bold yellow]Press Enter to launch shell...[/bold yellow]")
        return True
    except Exception as e:
        rprint(f"[bold red]❌ Failed to save configuration: {e}[/bold red]")
        return False


# ── Helpers ──────────────────────────────────────────────────────────────────

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
    """Verify OpenRouter key validity by hitting its auth key status endpoint."""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        resp = requests.get("https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def _validate_nvidia_key(api_key: str) -> bool:
    """Verify NVIDIA NIM key validity by hitting its models endpoint and chat completions endpoint."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        resp = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers, timeout=10)
        if resp.status_code != 200:
            return False
            
        # Also try a lightweight ping request to chat completions
        payload = {
            "model": "nvidia/llama-3.1-nemotron-51b-instruct",
            "messages": [{"role": "user", "content": "Ping"}],
            "max_tokens": 1
        }
        resp_chat = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
        if resp_chat.status_code == 200:
            return True
            
        # Fallback to public free-tier model meta/llama-3.1-8b-instruct if default model is restricted
        payload["model"] = "meta/llama-3.1-8b-instruct"
        resp_chat_fallback = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers=headers, json=payload, timeout=10)
        return resp_chat_fallback.status_code == 200
    except Exception:
        return False



def ensure_openrouter_authenticated() -> str:
    """Check if OpenRouter key is set and valid, and guide the user through setting it if not."""
    from github_companion.services.config_service import get_openrouter_api_key, save_settings, _load
    
    key = get_openrouter_api_key()
    if key:
        with console.status("[bold yellow]Validating stored OpenRouter Key...[/bold yellow]", spinner="dots"):
            valid = _validate_openrouter_key(key)
        if valid:
            return key
        else:
            rprint("[bold red]⚠️ Stored OpenRouter API Key is invalid or expired.[/bold red]")

    rprint()
    rprint("[bold yellow]OpenRouter Configuration[/bold yellow]")
    rprint("It looks like OpenRouter has not been configured or needs re-authentication.")
    choice = console.input("Would you like to configure it now? (y/n) : ").strip().lower()
    if choice != "y":
        raise RuntimeError("OpenRouter is not configured.")

    while True:
        rprint("\n[bold white]Enter your OpenRouter API Key[/bold white]")
        new_key = get_masked_input("> ")
        if not new_key:
            continue

        with console.status("[bold yellow]Validating OpenRouter Key...[/bold yellow]", spinner="dots"):
            valid = _validate_openrouter_key(new_key)

        if valid:
            settings = _load()
            settings["openrouter_api_key"] = new_key
            save_settings(settings)
            rprint("\n[bold green]✓ OpenRouter Connected[/bold green]")
            rprint("[bold green]✓ API Key Verified[/bold green]")
            rprint("[bold green]✓ Configuration Saved[/bold green]\n")
            return new_key
        else:
            rprint("[bold red]❌ Invalid OpenRouter API Key. Please try again.[/bold red]")


def ensure_nvidia_authenticated() -> str:
    """Check if NVIDIA key is set and valid, and guide the user through setting it if not."""
    from github_companion.services.config_service import get_nvidia_api_key, save_settings, _load
    
    key = get_nvidia_api_key()
    if key:
        with console.status("[bold yellow]Validating stored NVIDIA API Key...[/bold yellow]", spinner="dots"):
            valid = _validate_nvidia_key(key)
        if valid:
            return key
        else:
            rprint("[bold red]⚠️ Stored NVIDIA API Key is invalid or expired.[/bold red]")

    rprint()
    rprint("[bold yellow]NVIDIA NIM Configuration[/bold yellow]")
    rprint("It looks like NVIDIA NIM has not been configured or needs re-authentication.")
    choice = console.input("Would you like to configure it now? (y/n) : ").strip().lower()
    if choice != "y":
        raise RuntimeError("NVIDIA NIM is not configured.")

    while True:
        rprint("\n[bold white]Enter your NVIDIA API Key[/bold white]")
        new_key = get_masked_input("> ")
        if not new_key:
            continue

        with console.status("[bold yellow]Validating NVIDIA API Key...[/bold yellow]", spinner="dots"):
            valid = _validate_nvidia_key(new_key)

        if valid:
            settings = _load()
            settings["nvidia_api_key"] = new_key
            save_settings(settings)
            rprint("\n[bold green]✓ NVIDIA Connected[/bold green]")
            rprint("[bold green]✓ API Key Verified[/bold green]")
            rprint("[bold green]✓ Configuration Saved[/bold green]\n")
            return new_key
        else:
            rprint("[bold red]❌ Invalid NVIDIA API Key. Please try again.[/bold red]")



