"""Workspace command — Manage default GC-Projects workspace."""
import os
import platform
from rich.console import Console
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from github_companion.services.config_service import _load, save_settings, get_default_workspace
from github_companion.utils.ui import error, success, info

console = Console()


def show_gc_workspace():
    """Handle GC > workspace command."""
    workspace_path = get_default_workspace()
    if not workspace_path:
        home = os.path.expanduser("~")
        workspace_path = os.path.join(home, "GC-Projects")
        os.makedirs(workspace_path, exist_ok=True)
        # Save it
        settings = _load()
        settings["workspace"] = workspace_path
        save_settings(settings)

    while True:
        # Count projects in workspace
        projects = []
        if os.path.exists(workspace_path):
            try:
                projects = [d for d in os.listdir(workspace_path) if os.path.isdir(os.path.join(workspace_path, d))]
            except Exception:
                pass

        from github_companion.services.theme_service import get_active_theme_obj
        theme = get_active_theme_obj()
        from rich import box
        content = []
        content.append(f"  [{theme.highlight}]Workspace Location :[/{theme.highlight}] [cyan]{workspace_path}[/cyan]")
        content.append(f"  [{theme.highlight}]Total Projects     :[/{theme.highlight}] [cyan]{len(projects)}[/cyan]")
        content.append("")
        content.append("[bold white]Options:[/bold white]")
        content.append(f"  [{theme.command}]1[/{theme.command}]. Open Workspace folder")
        content.append(f"  [{theme.command}]2[/{theme.command}]. Change Workspace location")
        content.append(f"  [{theme.command}]3[/{theme.command}]. Create New Project")
        content.append(f"  [{theme.command}]4[/{theme.command}]. List Projects")
        content.append(f"  [{theme.command}]5[/{theme.command}]. Back to GC shell")
        
        panel = Panel(
            "\n".join(content),
            title=f"[bold {theme.header}] Workspace Management [/bold {theme.header}]",
            border_style=theme.border,
            box=box.ROUNDED,
            expand=False
        )
        console.print()
        console.print(panel)
        console.print()

        choice = console.input("[bold yellow]Select option (1-5) : [/bold yellow]").strip()

        if choice == "1":
            from github_companion.services.system_service import open_directory
            try:
                open_directory(workspace_path)
                success("Workspace folder opened.")
            except Exception as e:
                error(f"Could not open workspace: {e}")
        elif choice == "2":
            new_ws = console.input("\nEnter new workspace path: ").strip()
            if new_ws:
                resolved_path = os.path.abspath(os.path.expanduser(new_ws))
                if not (resolved_path.endswith("GC-Projects") or resolved_path.endswith("GC-Projects/")):
                    resolved_path = os.path.join(resolved_path, "GC-Projects")
                
                if not os.path.exists(resolved_path):
                    rprint(f"[bold yellow]Directory '{resolved_path}' does not exist.[/bold yellow]")
                    create = console.input("Create it? (y/n) : ").strip().lower()
                    if create == "y":
                        try:
                            os.makedirs(resolved_path, exist_ok=True)
                            success(f"Workspace path created.")
                        except Exception as e:
                            error(f"Failed to create directory: {e}")
                            continue
                    else:
                        continue
                
                settings = _load()
                settings["workspace"] = resolved_path
                save_settings(settings)
                workspace_path = resolved_path
                success("Workspace location updated successfully.")
        elif choice == "3":
            from github_companion.commands.code import start_code_mode
            start_code_mode()
            break
        elif choice == "4":
            from github_companion.commands.projects import show_gc_projects
            show_gc_projects()
            break
        elif choice == "5" or choice.lower() in ("exit", "back"):
            break
        else:
            error("Invalid choice.")
