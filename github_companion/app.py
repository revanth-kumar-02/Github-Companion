"""Entry point for github-companion."""
import sys
import os

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

from github_companion.commands.version import show_gc_version
from github_companion.commands.status import show_gc_status
from github_companion.commands.help import show_help
from github_companion.commands.latest import show_gc_latest
from github_companion.commands.pushed import show_gc_push
from github_companion.commands.profile import show_gc_profile
from github_companion.commands.repos import show_gc_repo
from github_companion.commands.heatmap import show_gc_heatmap
from github_companion.commands.create import create_repos
from github_companion.commands.delete import delete_repo
from github_companion.commands.rename import rename_repo
from github_companion.commands.publish import show_gc_publish
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
from github_companion.utils.ui import header
from github_companion.shell import start_shell


def main():
    # ── Fast path for version and help flags before configuration check ─────────
    if len(sys.argv) > 1:
        initial_flag = sys.argv[1].lower().strip()
        if initial_flag in ("--version", "-v", "version"):
            show_gc_version()
            return
        if initial_flag in ("--help", "-h", "help"):
            show_help()
            return

    from github_companion.services.config_service import is_configured, run_startup_diagnostics
    from github_companion.services.setup_wizard import run_setup_wizard
    from github_companion.services.theme_service import validate_themes_startup

    # Run theme registry and configuration safety checks first
    validate_themes_startup()

    run_startup_diagnostics()

    if not is_configured():
        if not sys.stdin.isatty():
            print(
                "Error: GitHub Companion is not configured. Run 'gc' interactively to set up.",
                file=sys.stderr,
            )
            sys.exit(1)
        success = run_setup_wizard()
        if not success:
            sys.exit(1)

    if len(sys.argv) == 1:
        start_shell()
        return

    command = sys.argv[1].lower().strip()

    commands = {
        "version": show_gc_version,
        "--version": show_gc_version,
        "-v": show_gc_version,
        "help": show_help,
        "--help": show_help,
        "-h": show_help,
        "status": show_gc_status,
        "latest": show_gc_latest,
        "pushed": show_gc_push,
        "profile": show_gc_profile,
        "repos": show_gc_repo,
        "heatmap": show_gc_heatmap,
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

    if command in commands:
        try:
            if command in ("config", "doctor", "theme", "tutor"):
                commands[command](sys.argv[2:])
            else:
                commands[command]()
        except Exception as e:
            from github_companion.utils.ui import show_exception_panel
            show_exception_panel(e, f"CLI Command execution failed: '{command}'")
    else:
        show_help()


if __name__ == "__main__":
    main()
