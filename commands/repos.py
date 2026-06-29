from services.github_service import get_github_repositories

def show_gc_repo():
    repo = get_github_repositories()
    print(repo)