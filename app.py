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
from utils.ui import header
from shell import start_shell


def main():

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
    }

    if command in commands:
        commands[command]()
    else:
        show_help()


if __name__ == "__main__":
    main()

