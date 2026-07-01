from services.github_service import repo_create
from utils.ui import success, error
from rich import print


def create_repos():
    repo_name = input("Repository Name : ")
    description = input("Description : ")
    repo_type = input("Private? (y/n): ").lower()

    response = repo_create(
        repo_name,
        description,
        repo_type == "y"
    )

    if response.status_code == 201:
        if response.status_code == 201:
            repo = response.json()
            print()
            success(f"Repository '{repo_name}' created successfully.")
            print(f"[bold cyan]🌐 Repository URL :[/bold cyan] [underline blue]{repo['html_url']}[/underline blue]")
            



    else:
        error("Failed to create repository.")
        print(response.json())  