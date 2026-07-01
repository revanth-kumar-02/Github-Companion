from utils.ui import header
from rich.console import Console
from utils.ui import header

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
    "rename" : rename_repo
}

def start_shell():
    header()
    while True:
        user_input = console.input("[bold blue]GC > [/bold blue]").strip().lower()
        if user_input in commands:
            commands[user_input]()
            continue
        
        if user_input in ("exit", "quit"):
            console.print("[green]Goodbye![/green]")
            break
        
        console.print(f"[red]Unknown command:[/red] {user_input}")
        console.print("Type 'help' to see available commands.")

if __name__ == "__main__":
    start_shell()