from services.git_service import get_git_status


def show_gc_push():
    status = get_git_status()
    print("Git Push Status")
    print("---------------------------")
    if "up to date" in status:
        print("✅ Latest commit is pushed.")
    else:
        print("⚠ Latest commit is NOT pushed.")
        
        
    
