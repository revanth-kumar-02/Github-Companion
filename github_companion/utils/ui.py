from rich import print
from github_companion.services.theme_service import get_active_theme_obj

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

    print(f"[{theme.banner}]{banner}[/{theme.banner}]")
    print(f"[{theme.header}]GitHub Companion[/{theme.header}]")
    print("[dim]Developer CLI • v0.1.1[/dim]")
    print(f"[{theme.border}]" + "─" * 42 + f"[/{theme.border}]")


def success(message):
    theme = get_active_theme_obj()
    print(f"[{theme.success}]✅ {message}[/{theme.success}]")   


def warning(message):
    theme = get_active_theme_obj()
    print(f"[{theme.warning}]⚠️ {message}[/{theme.warning}]")


def error(message):
    theme = get_active_theme_obj()
    print(f"[{theme.error}]❌ {message}[/{theme.error}]")


def info(message):
    theme = get_active_theme_obj()
    print(f"[{theme.highlight}]ℹ️ {message}[/{theme.highlight}]")