from services.git_service import get_latest_commit
from rich import print

def show_gc_latest():
    latest = get_latest_commit()
    print()
    print("Git Latest Commit: ")
    print("[white]" + "─" * 47 + "[/white]")
    print()
    print(latest)
    print()
    print("[white]" + "─" * 47 + "[/white]")
