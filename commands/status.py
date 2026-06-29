from services.git_service import get_git_status

status = get_git_status()

def show_gc_status():
    print()
    print("Git Status: ")
    print("═══════════════════════════════════════════════════")
    print()
    print(status)
    
    print()
    print("═══════════════════════════════════════════════════")


