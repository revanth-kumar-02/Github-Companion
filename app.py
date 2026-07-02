"""Entry point for github-companion."""
import sys
from commands.version import show_gc_version
from commands.status import show_gc_status
from commands.help import show_help
from commands.latest import show_gc_latest
from commands.pushed import show_gc_push
from commands.profile import show_gc_profile
from commands.repos import show_gc_repo
from commands.heatmap import show_gc_heatmap
from commands.create import create_repos
from commands.delete import delete_repo
from commands.rename import rename_repo
from commands.publish import show_gc_publish
from commands.search import gc_search
from commands.readme import show_gc_readme
from commands.ai_cmd import start_ai_mode
from commands.ask import start_ask_mode
from commands.code import start_code_mode
from commands.models import show_models_menu
from commands.login import login_cmd
from commands.logout import logout_cmd
from commands.config import config_cmd
from commands.doctor import doctor_cmd
from commands.auth import auth_cmd
from utils.ui import header
from shell import start_shell


def main():
    from services.config_service import is_configured
    from services.setup_wizard import run_setup_wizard

    if not is_configured():
        success = run_setup_wizard()
        if not success:
            sys.exit(1)

    if len(sys.argv) == 1:
        start_shell()
        return

    header()

    command = sys.argv[1].lower()

    commands = {
        "version": show_gc_version,
        "status": show_gc_status,
        "latest": show_gc_latest,
        "pushed": show_gc_push,
        "profile": show_gc_profile,
        "repos": show_gc_repo,
        "heatmap": show_gc_heatmap,
        "help": show_help,
        "create": create_repos,
        "delete" : delete_repo,
        "rename": rename_repo,
        "publish": show_gc_publish,
        "search": gc_search,
        "readme": show_gc_readme,
        "ai": start_ai_mode,
        "ask": start_ask_mode,
        "code": start_code_mode,
        "models": show_models_menu,
        "login": login_cmd,
        "logout": logout_cmd,
        "config": config_cmd,
        "doctor": doctor_cmd,
        "auth": auth_cmd,
    }


    if command in commands:
        if command in ("config", "doctor"):
            commands[command](sys.argv[2:])
        else:
            commands[command]()
    else:
        show_help()


if __name__ == "__main__":
    main()


