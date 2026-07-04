"""Projects command — manage generated projects in GC-Projects."""
import os
import platform
from rich.console import Console
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from github_companion.services.config_service import get_default_workspace, get_github_username, _load
from github_companion.utils.ui import error, success, info

console = Console()


def show_gc_projects():
    """Handle GC > projects command."""
    workspace_path = get_default_workspace()
    if not workspace_path:
        home = os.path.expanduser("~")
        workspace_path = os.path.join(home, "GC-Projects")
        os.makedirs(workspace_path, exist_ok=True)

    while True:
        # Load directories
        if not os.path.exists(workspace_path):
            rprint("[bold yellow]Workspace directory does not exist. Creating it...[/bold yellow]")
            os.makedirs(workspace_path, exist_ok=True)

        try:
            dirs = sorted([d for d in os.listdir(workspace_path) if os.path.isdir(os.path.join(workspace_path, d))])
        except Exception as e:
            error(f"Failed to list workspace projects: {e}")
            break

        rprint()
        rprint("[bold bright_white]==========================================[/bold bright_white]")
        rprint("[bold bright_white]                 PROJECTS                 [/bold bright_white]")
        rprint("[bold bright_white]==========================================[/bold bright_white]")
        rprint()

        if not dirs:
            rprint("  [dim]No projects found in workspace.[/dim]")
            rprint()
            rprint("  [bold cyan]1[/bold cyan]. Create New Project")
            rprint("  [bold cyan]2[/bold cyan]. Back to GC shell")
            rprint()
            choice = console.input("[bold yellow]Select option (1-2) : [/bold yellow]").strip()
            if choice == "1":
                from github_companion.commands.code import start_code_mode
                start_code_mode()
                break
            else:
                break

        for idx, d in enumerate(dirs, 1):
            rprint(f"  [bold cyan]{idx}[/bold cyan]. {d}")

        rprint()
        rprint("  [bold cyan]B[/bold cyan]. Back to GC shell")
        rprint()

        choice = console.input("[bold yellow]Select a project index or action (B) : [/bold yellow]").strip()
        if choice.upper() == "B":
            break

        try:
            val = int(choice)
            if 1 <= val <= len(dirs):
                selected_project = dirs[val - 1]
                _project_actions_menu(workspace_path, selected_project)
            else:
                error("Invalid selection index.")
        except ValueError:
            error("Invalid option.")


def _project_actions_menu(workspace_path: str, project_name: str) -> None:
    project_path = os.path.join(workspace_path, project_name)
    while True:
        rprint()
        rprint(f"[bold bright_white]Project: {project_name}[/bold bright_white]")
        rprint("[blue]" + "─" * 47 + "[/blue]")
        rprint(f"  Location: [cyan]{project_path}[/cyan]")
        rprint()

        rprint("[bold white]Actions:[/bold white]")
        rprint("  [bold cyan]1[/bold cyan]. Open Project folder")
        rprint("  [bold cyan]2[/bold cyan]. Open in VS Code")
        rprint("  [bold cyan]3[/bold cyan]. Run Project")
        rprint("  [bold cyan]4[/bold cyan]. Publish to GitHub")
        rprint("  [bold cyan]5[/bold cyan]. View README.md")
        rprint("  [bold cyan]6[/bold cyan]. Delete Project")
        rprint("  [bold cyan]7[/bold cyan]. Rename Project folder")
        rprint("  [bold cyan]8[/bold cyan]. Project Information")
        rprint("  [bold cyan]9[/bold cyan]. Back to Projects list")
        rprint()

        action = console.input("[bold yellow]Select action (1-9) : [/bold yellow]").strip()

        if action == "1":
            from github_companion.services.system_service import open_directory
            try:
                open_directory(project_path)
                success("Project folder opened.")
            except Exception as e:
                error(f"Could not open project: {e}")

        elif action == "2":
            from github_companion.services.system_service import launch_vscode
            try:
                launch_vscode(project_path)
                success("VS Code launched.")
            except Exception as e:
                error(f"Could not open in VS Code: {e}")

        elif action == "3":
            # Run project: check for entry point
            entry = None
            if os.path.exists(os.path.join(project_path, "app.py")):
                entry = "app.py"
            elif os.path.exists(os.path.join(project_path, "main.py")):
                entry = "main.py"
            elif os.path.exists(os.path.join(project_path, "index.js")):
                entry = "index.js"

            if entry:
                rprint(f"[bold yellow]Running Project ({entry})...[/bold yellow]")
                from github_companion.services.system_service import run_project_file
                try:
                    run_project_file(project_path, entry)
                    success("Project run command launched in a separate window.")
                except Exception as e:
                    error(f"Failed to run project: {e}")
            else:
                error("No run entry point (app.py, main.py, or index.js) found.")

        elif action == "4":
            from github_companion.services.git_service import git_push, git_remote_add, git_remote
            from github_companion.services.github_service import repo_create
            
            remote_out = git_remote(project_path)
            if "origin" in remote_out:
                rprint("[bold yellow]Origin remote already exists. Pushing...[/bold yellow]")
                try:
                    git_push(project_path)
                    success("Push completed successfully.")
                except Exception as e:
                    error(f"Push failed: {e}")
            else:
                rprint("[bold purple]Creating GitHub repository...[/bold purple]")
                resp = repo_create(project_name, "Generated project by GitHub Companion", private=False)
                if resp.status_code == 201:
                    repo_data = resp.json()
                    repo_url = repo_data["html_url"]
                    username = get_github_username()
                    remote_url = f"https://{username}@github.com/{username}/{project_name}.git"

                    try:
                        git_remote_add(project_path, remote_url)
                        git_push(project_path)
                        success(f"GitHub Repository Successfully Created & Pushed: {repo_url}")
                    except Exception as e:
                        error(f"Push failed: {e}")
                else:
                    error(f"Failed to create repository: {resp.json().get('message', 'Unknown error')}")

        elif action == "5":
            readme_path = os.path.join(project_path, "README.md")
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        rprint(Panel(f.read(), title="README.md", border_style="cyan"))
                except Exception as e:
                    error(f"Could not read README.md: {e}")
            else:
                error("README.md not found.")

        elif action == "6":
            confirm = console.input("[bold red]Are you absolutely sure you want to delete this project locally? (y/n) : [/bold red]").strip().lower()
            if confirm in ("y", "yes"):
                import shutil
                try:
                    shutil.rmtree(project_path)
                    success(f"Project '{project_name}' deleted successfully.")
                    break
                except Exception as e:
                    error(f"Failed to delete project: {e}")

        elif action == "7":
            new_name = console.input("\nEnter new project folder name: ").strip()
            if new_name:
                import re
                new_folder = re.sub(r'[^a-zA-Z0-9\s\-]', '', new_name).strip().replace(" ", "-").lower()
                new_path = os.path.join(workspace_path, new_folder)
                if os.path.exists(new_path):
                    error("A folder with that name already exists.")
                else:
                    try:
                        os.rename(project_path, new_path)
                        success(f"Folder renamed to '{new_folder}'.")
                        project_name = new_folder
                        project_path = new_path
                    except Exception as e:
                        error(f"Rename failed: {e}")

        elif action == "8":
            files = []
            loc = 0
            for root, _, fs in os.walk(project_path):
                if ".git" in root or "__pycache__" in root:
                    continue
                for f in fs:
                    fp = os.path.join(root, f)
                    files.append(os.path.relpath(fp, project_path))
                    try:
                        with open(fp, "r", errors="ignore") as f_obj:
                            loc += len(f_obj.readlines())
                    except Exception:
                        pass
            
            info_table = Table(show_header=True, header_style="bold yellow", border_style="cyan")
            info_table.add_column("Property", style="bold cyan")
            info_table.add_column("Details", style="white")
            info_table.add_row("Files Count", str(len(files)))
            info_table.add_row("Total LOC", f"{loc} lines")
            
            from github_companion.services.git_service import git_log_oneline
            log_out = git_log_oneline(project_path)
            info_table.add_row("Last Commit", log_out.strip() or "No Commits")
            
            console.print(Panel(info_table, title="Project Details", border_style="cyan", expand=False))

        elif action == "9":
            break
        else:
            error("Invalid action.")
