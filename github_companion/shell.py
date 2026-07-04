import sys

# Force standard streams to use UTF-8 to prevent CP1252 encoder crashes on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from github_companion.commands.publish import show_gc_publish
from github_companion.utils.ui import header
from rich.console import Console

from github_companion.commands.create import create_repos
from github_companion.commands.delete import delete_repo
from github_companion.commands.rename import rename_repo
from github_companion.commands.profile import show_gc_profile
from github_companion.commands.repos import show_gc_repo
from github_companion.commands.status import show_gc_status
from github_companion.commands.latest import show_gc_latest
from github_companion.commands.pushed import show_gc_push
from github_companion.commands.version import show_gc_version
from github_companion.commands.help import show_help
from github_companion.commands.heatmap import show_gc_heatmap
from github_companion.commands.search import gc_search
from github_companion.commands.readme import show_gc_readme
from github_companion.commands.ai_cmd import start_ai_mode
from github_companion.commands.ask import start_ask_mode, start_chat_mode
from github_companion.commands.code import start_code_mode, start_plan_mode
from github_companion.commands.models import show_models_menu
from github_companion.commands.login import login_cmd
from github_companion.commands.logout import logout_cmd
from github_companion.commands.config import config_cmd
from github_companion.commands.doctor import doctor_cmd
from github_companion.commands.auth import auth_cmd
from github_companion.commands.workspace import show_gc_workspace
from github_companion.commands.projects import show_gc_projects
from github_companion.commands.theme import theme_cmd
from github_companion.commands.tutor import tutor_cmd
from github_companion.commands.clone import clone_repo
from github_companion.commands.dashboard import show_gc_dashboard

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
    "theme": theme_cmd,
    "tutor": tutor_cmd,
    "clone": clone_repo,
    "dashboard": show_gc_dashboard,
}


def start_shell():
    header()
    while True:
        from github_companion.services.theme_service import get_active_theme_obj
        theme = get_active_theme_obj()
        try:
            user_input = console.input(f"[{theme.prompt}]GC > [/{theme.prompt}]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[{theme.success}]Goodbye![/{theme.success}]")
            break

        if not user_input:
            continue

        parts = user_input.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in commands:
            try:
                if cmd in ("config", "doctor", "theme", "tutor"):
                    commands[cmd](args)
                else:
                    commands[cmd]()
            except Exception as e:
                from github_companion.utils.ui import show_exception_panel
                show_exception_panel(e, f"Shell Command execution failed: '{cmd}'")
            continue

        if cmd in ("exit", "quit"):
            console.print(f"[{theme.success}]Goodbye![/{theme.success}]")
            break

        console.print(f"[{theme.error}]Unknown command:[/{theme.error}] {cmd}")
        console.print("Type 'help' to see available commands.")


if __name__ == "__main__":
    start_shell()
