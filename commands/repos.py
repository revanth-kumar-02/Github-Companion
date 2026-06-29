from services.github_service import get_github_repositories
from rich import print 

def show_gc_repo():
    print()
    print("Public Repositories")
    print("[white]" + "─" * 47 + "[/white]")
    print()
    repo = get_github_repositories()
    
    print(repo)