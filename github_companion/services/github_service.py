"""GitHub API service with timeouts, authentication headers, and safe error handling."""
from __future__ import annotations
import requests
from github_companion.services.config_service import get_github_token, get_github_username
from github_companion.utils.constants import GITHUB_API

DEFAULT_TIMEOUT = 10


def _get_headers(token: str | None = None, content_type: bool = False) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Companion-CLI",
    }
    tok = token if token is not None else get_github_token()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    if content_type:
        headers["Content-Type"] = "application/json"
    return headers


def get_github_profile() -> dict:
    """Fetch GitHub profile data for the configured username."""
    username = get_github_username()
    if not username:
        return {"message": "GitHub username is not configured."}

    headers = _get_headers()
    try:
        response = requests.get(
            f"{GITHUB_API}/users/{username}",
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        return {"message": f"GitHub API error (Status {response.status_code})"}
    except requests.RequestException as exc:
        return {"message": f"Network error fetching profile: {exc}"}


def get_github_repositories() -> list[dict]:
    """Fetch all repositories for the configured user."""
    username = get_github_username()
    token = get_github_token()
    headers = _get_headers(token)

    url = f"{GITHUB_API}/user/repos" if token else f"{GITHUB_API}/users/{username}/repos"

    try:
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return []


def fetch_repositories(limit: int = 30) -> list[dict]:
    """Return repository data as a list of dicts (used by AI tools layer)."""
    username = get_github_username()
    token = get_github_token()
    headers = _get_headers(token)

    try:
        response = requests.get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=headers,
            params={"per_page": min(limit, 30), "sort": "updated"},
            timeout=DEFAULT_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass
    return []


def repo_create(repo_name: str, description: str, private: bool) -> requests.Response:
    """Create a new GitHub repository."""
    headers = _get_headers(content_type=True)
    return requests.post(
        f"{GITHUB_API}/user/repos",
        headers=headers,
        json={
            "name": repo_name,
            "description": description,
            "private": private,
        },
        timeout=DEFAULT_TIMEOUT,
    )


def repo_delete(repo_name: str) -> requests.Response:
    """Delete a GitHub repository."""
    username = get_github_username()
    headers = _get_headers()
    return requests.delete(
        f"{GITHUB_API}/repos/{username}/{repo_name}",
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
    )


def search_repositories(keyword: str) -> requests.Response:
    """Search authenticated user's repositories by keyword."""
    username = get_github_username()
    headers = _get_headers()
    query = f"{keyword} user:{username}"
    return requests.get(
        f"{GITHUB_API}/search/repositories",
        headers=headers,
        params={"q": query, "per_page": 30, "sort": "updated"},
        timeout=DEFAULT_TIMEOUT,
    )


def repo_rename(old_name: str, new_name: str) -> requests.Response:
    """Rename a GitHub repository."""
    username = get_github_username()
    headers = _get_headers(content_type=True)
    return requests.patch(
        f"{GITHUB_API}/repos/{username}/{old_name}",
        headers=headers,
        json={"name": new_name},
        timeout=DEFAULT_TIMEOUT,
    )