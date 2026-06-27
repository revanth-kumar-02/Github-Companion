from services.git_service import get_latest_commit

def show_gc_latest():
    latest = get_latest_commit()
    print("Git Latest Commit: ")
    
    print(latest)
