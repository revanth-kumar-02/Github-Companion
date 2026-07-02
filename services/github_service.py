from services.config_service import get_github_token, get_github_username
from utils.constants import GITHUB_API
import requests

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

def fetch_repositories(limit: int = 30) -> list:
    """Return repository data as a list of dicts (used by AI tools layer)."""
    username = get_github_username()
    token = get_github_token()
    response = requests.get(
        f"{GITHUB_API}/users/{username}/repos",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        params={"per_page": limit, "sort": "updated"},
        timeout=10,
    )
    if response.status_code == 200:
        return response.json()
    return []






def repo_create(repo_name, description, private):
    headers = {
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

def repo_delete(repo_name):
    username = get_github_username()

    headers = {
        "Authorization": f"Bearer {get_github_token()}",
        "Accept": "application/vnd.github+json",
    }
    url = f"{GITHUB_API}/repos/{username}/{repo_name}"
    response = requests.delete(
        f"{GITHUB_API}/repos/{username}/{repo_name}",
        headers=headers,
        timeout=10,
    )

    return response

def search_repositories(keyword):
    """Search authenticated user's repositories by keyword using GitHub Search API."""
    username = get_github_username()
    token = get_github_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    query = f"{keyword} user:{username}"
    response = requests.get(
        f"{GITHUB_API}/search/repositories",
        headers=headers,
        params={"q": query, "per_page": 30, "sort": "updated"},
        timeout=10,
    )
    return response


def repo_rename(old_name, new_name):
    username = get_github_username()

    headers = {
        "Authorization": f"Bearer {get_github_token()}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }

    response = requests.patch(
        f"{GITHUB_API}/repos/{username}/{old_name}",
        headers=headers,
        json={
            "name": new_name
        },
        timeout=10,
    )

    return response