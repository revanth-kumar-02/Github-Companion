from services.git_service import get_git_status
from rich import print

status = get_git_status()

def show_gc_status():
    print()
    print("Git Status: ")
    print("[white]" + "─" * 47 + "[/white]")
    print()
    print(status)
    
    print()
    print("[white]" + "─" * 47 + "[/white]")


