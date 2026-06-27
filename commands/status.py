from services.git_service import get_git_status

def show_gc_status():
    status = get_git_status()
    print("Git Status: ")
    print(status)
