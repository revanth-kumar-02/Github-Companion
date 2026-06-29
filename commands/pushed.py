from services.git_service import get_git_status
from rich import print

def show_gc_push():
    status = get_git_status()
    print()
    print("Git Push Status")
    print("[white]" + "─" * 47 + "[/white]")
    print()
    if "up to date" in status:
        print("✅ Latest commit is pushed.")
    else:
        print("⚠ Latest commit is NOT pushed.")
    print()
    print("[white]" + "─" * 47 + "[/white]")
        
        
    
