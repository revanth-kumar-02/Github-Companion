from commands.publish import show_gc_publish
from utils.ui import header
from rich.console import Console

from commands.create import create_repos
from commands.delete import delete_repo
from commands.rename import rename_repo
from commands.profile import show_gc_profile
from commands.repos import show_gc_repo
from commands.status import show_gc_status
from commands.latest import show_gc_latest
from commands.pushed import show_gc_push
from commands.version import show_gc_version
from commands.help import show_help
from commands.heatmap import show_gc_heatmap
from commands.search import gc_search
from commands.readme import show_gc_readme
from commands.ai_cmd import start_ai_mode
from commands.ask import start_ask_mode, start_chat_mode
from commands.code import start_code_mode, start_plan_mode
from commands.models import show_models_menu
from commands.login import login_cmd
from commands.logout import logout_cmd
from commands.config import config_cmd
from commands.doctor import doctor_cmd
from commands.auth import auth_cmd
from commands.workspace import show_gc_workspace
from commands.projects import show_gc_projects

console = Console()

commands = {
    "profile": show_gc_profile,
    "repos": show_gc_repo,
    "status": show_gc_status,
    "latest": show_gc_latest,
    "pushed": show_gc_push,
    "version": show_gc_version,
    "heatmap": show_gc_heatmap,
    "help": show_help,
    "create": create_repos,
    "delete": delete_repo,
    "rename": rename_repo,
    "publish": show_gc_publish,
    "search": gc_search,
    "readme": show_gc_readme,
    "ai": start_ai_mode,
    "ask": start_ask_mode,
    "chat": start_chat_mode,
    "code": start_code_mode,
    "plan": start_plan_mode,
    "models": show_models_menu,
    "login": login_cmd,
    "logout": logout_cmd,
    "config": config_cmd,
    "doctor": doctor_cmd,
    "auth": auth_cmd,
    "workspace": show_gc_workspace,
    "projects": show_gc_projects,
}


def start_shell():
    header()
    while True:
        try:
            user_input = console.input("[bold blue]GC > [/bold blue]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[green]Goodbye![/green]")
            break

        if not user_input:
            continue

        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in commands:
            if cmd in ("config", "doctor"):
                commands[cmd](args)
            else:
                commands[cmd]()
            continue

        if cmd in ("exit", "quit"):
            console.print("[green]Goodbye![/green]")
            break

        console.print(f"[red]Unknown command:[/red] {cmd}")
        console.print("Type 'help' to see available commands.")


if __name__ == "__main__":
    start_shell()