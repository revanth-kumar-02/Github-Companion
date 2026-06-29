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
from utils.ui import header


def main():
    header()

    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()

    commands = {
        "version": show_gc_version,
        "status": show_gc_status,
        "latest": show_gc_latest,
        "pushed": show_gc_push,
        "profile": show_gc_profile,
        "repos" : show_gc_repo,
        "heatmap" : show_gc_heatmap,
        "help": show_help,
    }

    if command in commands:
        commands.get(command)()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        show_help()


if __name__ == "__main__":
    main()

