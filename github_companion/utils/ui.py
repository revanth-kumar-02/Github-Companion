from rich import print
import os
import sys
import traceback
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from github_companion.services.theme_service import get_active_theme_obj

console = Console()

def header():
    theme = get_active_theme_obj()
    banner = r"""
 ██████╗  ██████╗
██╔════╝ ██╔════╝
██║  ███╗██║
██║   ██║██║
╚██████╔╝╚██████╗
 ╚═════╝ ╚═════╝
    """
    
    banner_text = Text(banner, style=theme.banner)
    
    try:
        from github_companion.services.config_service import (
            get_default_workspace,
            get_github_username,
            get_ai_provider,
            get_coding_model
        )
        from github_companion.services.git_service import get_git_version
        
        workspace = get_default_workspace() or "Not Configured"
        username = get_github_username() or "Guest"
        provider = get_ai_provider() or "Ollama"
        model = get_coding_model() or "N/A"
        
        try:
            git_ver = get_git_version()
            git_status = f"Installed ({git_ver.strip()})" if git_ver else "Not Installed"
        except Exception:
            git_status = "Not Installed"
            
        auth_status = "Authenticated" if get_github_username() else "Local Mode"
    except Exception:
        workspace = "N/A"
        username = "Guest"
        provider = "N/A"
        model = "N/A"
        git_status = "Unknown"
        auth_status = "Unknown"

    dashboard_table = Table.grid(expand=True, padding=(0, 2))
    dashboard_table.add_column(ratio=1)
    dashboard_table.add_column(ratio=1)
    
    left_side = Text()
    left_side.append("🔧 ENVIRONMENT\n", style=f"bold {theme.highlight}")
    left_side.append("  Version   : ", style="bold white")
    left_side.append("v0.1.1\n", style="white")
    left_side.append("  Workspace : ", style="bold white")
    left_side.append(f"{workspace}\n", style="cyan")
    left_side.append("  User      : ", style="bold white")
    left_side.append(f"{username} ({auth_status})\n", style="green" if auth_status == "Authenticated" else "yellow")
    
    right_side = Text()
    right_side.append("🤖 AI SETTINGS\n", style=f"bold {theme.highlight}")
    right_side.append("  Provider  : ", style="bold white")
    right_side.append(f"{provider.upper()}\n", style="cyan")
    right_side.append("  Model     : ", style="bold white")
    right_side.append(f"{model}\n", style="cyan")
    right_side.append("  Theme     : ", style="bold white")
    right_side.append(f"{theme.name.capitalize()}\n", style="green")
    
    dashboard_table.add_row(left_side, right_side)
    
    status_text = Text()
    status_text.append("\n🩺 SYSTEM STATUS\n", style=f"bold {theme.highlight}")
    status_text.append("  Git CLI   : ", style="bold white")
    status_text.append(f"{git_status}\n", style="green" if "Installed" in git_status else "red")
    status_text.append("  Status    : ", style="bold white")
    status_text.append("Ready for action ⚡", style="bold green")
    
    main_group = Table.grid(expand=True)
    main_group.add_row(banner_text)
    main_group.add_row(Text("GitHub Companion - AI Developer CLI\n", style=f"bold {theme.header}"))
    main_group.add_row(dashboard_table)
    main_group.add_row(status_text)
    
    panel = Panel(
        main_group,
        border_style=theme.border,
        box=box.ROUNDED,
        title=f"[{theme.header}] GitHub Companion Dashboard [/{theme.header}]",
        title_align="center",
        expand=False
    )
    
    console.print()
    console.print(panel)
    console.print()

def success(message):
    theme = get_active_theme_obj()
    console.print(f"[{theme.success}]✅ {message}[/{theme.success}]")   

def warning(message):
    theme = get_active_theme_obj()
    console.print(f"[{theme.warning}]⚠️ {message}[/{theme.warning}]")

def error(message):
    theme = get_active_theme_obj()
    console.print(f"[{theme.error}]❌ {message}[/{theme.error}]")

def info(message):
    theme = get_active_theme_obj()
    console.print(f"[{theme.highlight}]ℹ️ {message}[/{theme.highlight}]")

def show_error_panel(message, title="Error"):
    theme = get_active_theme_obj()
    panel = Panel(
        Text(f"❌ {message}", style="white"),
        title=f"[bold {theme.error}]{title}[/bold {theme.error}]",
        border_style=theme.error,
        box=box.ROUNDED,
        expand=False
    )
    console.print(panel)

def show_success_panel(message, title="Success"):
    theme = get_active_theme_obj()
    panel = Panel(
        Text(f"✅ {message}", style="white"),
        title=f"[bold {theme.success}]{title}[/bold {theme.success}]",
        border_style=theme.success,
        box=box.ROUNDED,
        expand=False
    )
    console.print(panel)

def show_warning_panel(message, title="Warning"):
    theme = get_active_theme_obj()
    panel = Panel(
        Text(f"⚠️ {message}", style="white"),
        title=f"[bold {theme.warning}]{title}[/bold {theme.warning}]",
        border_style=theme.warning,
        box=box.ROUNDED,
        expand=False
    )
    console.print(panel)

def show_info_panel(message, title="Information"):
    theme = get_active_theme_obj()
    panel = Panel(
        Text(f"ℹ️ {message}", style="white"),
        title=f"[bold {theme.highlight}]{title}[/bold {theme.highlight}]",
        border_style=theme.border,
        box=box.ROUNDED,
        expand=False
    )
    console.print(panel)

def show_exception_panel(exc, context_info=None):
    theme = get_active_theme_obj()
    exc_type = type(exc).__name__
    exc_msg = str(exc)
    
    reason = exc_msg
    possible_cause = "Internal runtime execution logic issue."
    suggested_fix = "Check traceback details or settings."
    recovery_options = "Run 'gc doctor' to run diagnostics."
    
    if "ConnectionError" in exc_type or "Connection refused" in exc_msg or "offline" in exc_msg.lower() or "timeout" in exc_msg.lower():
        reason = "Failed to establish network connection."
        possible_cause = "Internet is disconnected, or local/remote server is down."
        suggested_fix = "Check connection, or verify the endpoint URL configured for provider."
        recovery_options = "Run 'gc doctor' or try again once connection is restored."
    elif "401" in exc_msg or "unauthorized" in exc_msg.lower() or "credentials" in exc_msg.lower() or "api_key" in exc_msg.lower():
        reason = "Authentication key rejected by provider API."
        possible_cause = "Misconfigured token, expired token, or missing environment variables."
        suggested_fix = "Run 'gc auth' or 'gc login' to update provider keys and GitHub token."
        recovery_options = "Verify keys in config via 'gc config'."
    elif "FileNotFoundError" in exc_type:
        reason = f"Required file was not found: {exc_msg}"
        possible_cause = "File deleted, path mismatch, or project folder restructured."
        suggested_fix = "Check path parameters or regenerate project files."
        recovery_options = "Verify GC workspace exists."

    content = Table.grid(expand=True, padding=(0, 1))
    content.add_column(style=f"bold {theme.error}", width=18)
    content.add_column(style="white")
    
    content.add_row("Error Type:", exc_type)
    content.add_row("Reason:", reason)
    content.add_row("Possible Cause:", possible_cause)
    content.add_row("Suggested Fix:", suggested_fix)
    content.add_row("Recovery Option:", recovery_options)
    if context_info:
        content.add_row("Context:", context_info)
        
    debug_mode = (
        os.environ.get("DEBUG") == "True"
        or os.environ.get("GC_DEBUG") == "true"
    )
    
    main_table = Table.grid(expand=True)
    main_table.add_row(content)
    
    if debug_mode:
        trace_str = traceback.format_exc()
        trace_panel = Panel(trace_str, title="[bold red]Technical Details (Debug)[/bold red]", border_style="red", box=box.ROUNDED)
        main_table.add_row(Text("\n"))
        main_table.add_row(trace_panel)
        
    panel = Panel(
        main_table,
        border_style=theme.error,
        box=box.ROUNDED,
        title=f"[bold {theme.error}] 🛑 System Exception Encountered [/bold {theme.error}]",
        expand=False
    )
    console.print()
    console.print(panel)
    console.print()