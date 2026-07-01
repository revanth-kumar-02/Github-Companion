from services.github_service import repo_rename
from utils.ui import success, error

def rename_repo():
    old_name = input("Current Repository Name : ")
    new_name = input("New Repository Name : ")

    response = repo_rename(old_name, new_name)

    if response.status_code == 200:
        success(f"Repository renamed to '{new_name}'.")
    else:
        error("Failed to rename repository.")
        print(response.json())