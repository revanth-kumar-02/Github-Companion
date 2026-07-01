
from utils.ui import success
from utils.ui import error


def create_repos():
    repo_name = input("Repository Name : ")
    descripation = input("Description : ")
    repo_type = input("Private? (y/n): ")
    response = create_repos(repo_name, descripation, repo_type)
    
    if response.status_code == 201:
        success(f"Repository '{repo_name}' created successfully.")
    else:
        error(" Failed to create repository.")