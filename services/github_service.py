from services.config_service import get_github_token, get_github_username
from utils.constants import GITHUB_API
import requests
from commands.create import create_repos

def get_github_profile():
    username = get_github_username()
    response = requests.get(f"{GITHUB_API}/users/{username}")
    return response.json()
    
def get_github_repositories():
    username = get_github_username()
    response = requests.get(f"{GITHUB_API}/users/{username}/repos")
    repos = response.json()
    for index,repo in enumerate(repos,start=1):
        print(f"{index}. {repo['name']}")




def repo_create(repo_name, description, private):
    headers={
    "Authorization": f"Bearer {get_github_token()}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json", 
    }
    response = requests.post(f"{GITHUB_API}/user/repos",
        headers=headers,
        json={
            "name": repo_name,
            "description": description,
            "private": private
        },
        timeout=10,
        )
    return response

def repo_delete():
    username = get_github_username()
    response = requests.delete(f"{GITHUB_API}/user/repos/{repo_name}", headers=headers)
    return response.json()

def repo_rename():
    username = get_github_username()
    response = requests.get(f"{GITHUB_API}/users/{username}/repos/{owner}/{repo}")
    return response.json()