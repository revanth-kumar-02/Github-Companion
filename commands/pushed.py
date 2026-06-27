from services.git_service import get_git_status




def show_gc_push():
    status = get_git_status()
    push_text = status
    print("Git Push Status")
    print("---------------------------")
    if "up to date" in push_text:
        print("✅ Latest commit is pushed.")
    else:
        print("⚠ Latest commit is NOT pushed.")
        
        
    
