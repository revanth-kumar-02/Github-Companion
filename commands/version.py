from services.git_service import get_git_version
from utils.ui import info
from rich import print

def show_gc_version():
    print()
    print("[white]" + "─" * 47 + "[/white]")
    version = get_git_version()
    info(" Git Version")
    print()
    print(version)
    print("[white]" + "─" * 47 + "[/white]")