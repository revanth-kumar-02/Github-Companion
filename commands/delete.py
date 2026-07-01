from services.github_service import repo_delete
from utils.ui import success, error

def delete_repo():
    repo_name = input("Repository Name : ")

    confirm = input(f"Delete '{repo_name}'? (y/n): ").lower()

    if confirm != "y":
        print("Cancelled.")
        return

    response = repo_delete(repo_name)

    if response.status_code == 204:
        success(f"Repository '{repo_name}' deleted successfully.")
    else:
        error("Failed to delete repository.")
        print(response.json())