"""
Tool registry for the GitHub Companion AI agent.

This module is the bridge between the LLM and the existing service layer.
It contains two things:

1. TOOL_SCHEMAS  — OpenAI function-calling JSON schemas the LLM receives.
2. execute_tool  — Routes each tool call to the correct service function
                   and returns a plain-text result the LLM can reason about.

Architecture rule: tools.py calls services. It never contains API logic itself.
"""
from __future__ import annotations
import os
import subprocess

from services.github_service import (
    repo_create,
    repo_delete,
    repo_rename,
    search_repositories,
    get_github_profile,
    fetch_repositories,
)
from services.git_service import (
    git_init,
    git_add,
    git_commit,
    git_branch,
    git_remote_add,
    git_push,
    get_git_status,
)
from services.readme_service import generate_readme
from services.config_service import get_github_username


# ── Tool Schemas (OpenAI function-calling format) ──────────────────────────────

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "create_repository",
            "description": "Create a new GitHub repository for the authenticated user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name":    {"type": "string",  "description": "Name of the repository to create"},
                    "description":  {"type": "string",  "description": "Short description of the repository"},
                    "private":      {"type": "boolean", "description": "True for private, False for public (default: False)"},
                },
                "required": ["repo_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_repository",
            "description": "Permanently delete an existing GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "Name of the repository to delete"},
                },
                "required": ["repo_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_repository",
            "description": "Rename an existing GitHub repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_name": {"type": "string", "description": "Current repository name"},
                    "new_name": {"type": "string", "description": "New repository name"},
                },
                "required": ["old_name", "new_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_repositories",
            "description": "Search the authenticated user's GitHub repositories by keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Search keyword or term"},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_profile",
            "description": "Get the authenticated GitHub user's profile information.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_repositories",
            "description": "List all repositories of the authenticated GitHub user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of repositories to return (default: 20, max: 30)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "publish_project",
            "description": (
                "Publish a local project folder to GitHub. "
                "Runs the complete workflow: create repository → git init → "
                "git add → git commit → rename branch to main → add remote → git push."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path":   {"type": "string",  "description": "Absolute or relative path to the project folder"},
                    "repo_name":      {"type": "string",  "description": "Name for the new GitHub repository"},
                    "description":    {"type": "string",  "description": "Repository description"},
                    "private":        {"type": "boolean", "description": "True for private, False for public"},
                    "commit_message": {"type": "string",  "description": "Initial commit message (default: 'Initial commit')"},
                },
                "required": ["project_path", "repo_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_readme",
            "description": "Generate a professional README.md file for a project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "output_folder":  {"type": "string", "description": "Folder where README.md will be written"},
                    "project_name":   {"type": "string", "description": "Name of the project"},
                    "description":    {"type": "string", "description": "One-line project description"},
                    "features":       {"type": "array",  "items": {"type": "string"}, "description": "List of key features"},
                    "installation":   {"type": "string", "description": "Installation command or steps"},
                    "usage":          {"type": "string", "description": "Usage command or example"},
                    "technologies":   {"type": "array",  "items": {"type": "string"}, "description": "Technologies and libraries used"},
                    "license":        {"type": "string", "description": "License type, e.g. MIT"},
                    "author":         {"type": "string", "description": "Author name"},
                },
                "required": ["output_folder", "project_name", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Get the Git status of a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to check (defaults to current directory)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List all files and subdirectories in a given directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list (defaults to current directory)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text contents of a file (capped at 8 KB).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read"},
                },
                "required": ["path"],
            },
        },
    },
]


# ── Tool Executor ──────────────────────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> str:
    """
    Route a tool call to the appropriate service function.

    Args:
        name : Tool name matching one of the TOOL_SCHEMAS entries.
        args : Parsed arguments dict from the LLM.

    Returns:
        A plain-text string the LLM will receive as the tool result.
    """
    try:
        return _DISPATCH[name](args)
    except KeyError:
        return f"Unknown tool: '{name}'"
    except Exception as exc:
        return f"Tool '{name}' raised an error: {exc}"


# ── Dispatcher helpers ─────────────────────────────────────────────────────────

def _create_repository(args: dict) -> str:
    resp = repo_create(
        args["repo_name"],
        args.get("description", ""),
        args.get("private", False),
    )
    if resp.status_code == 201:
        data = resp.json()
        return f"Repository '{args['repo_name']}' created. URL: {data['html_url']}"
    return f"Failed to create repository: {resp.json().get('message', 'Unknown error')}"


def _delete_repository(args: dict) -> str:
    resp = repo_delete(args["repo_name"])
    if resp.status_code == 204:
        return f"Repository '{args['repo_name']}' deleted successfully."
    return f"Failed to delete repository: {resp.json().get('message', 'Unknown error')}"


def _rename_repository(args: dict) -> str:
    resp = repo_rename(args["old_name"], args["new_name"])
    if resp.status_code == 200:
        return f"Repository renamed from '{args['old_name']}' to '{args['new_name']}'."
    return f"Failed to rename: {resp.json().get('message', 'Unknown error')}"


def _search_repositories(args: dict) -> str:
    resp = search_repositories(args["keyword"])
    if resp.status_code != 200:
        return f"Search failed: {resp.json().get('message', 'Unknown error')}"
    items = resp.json().get("items", [])
    if not items:
        return f"No repositories found matching '{args['keyword']}'."
    lines = [f"Found {len(items)} result(s) for '{args['keyword']}':"]
    for repo in items[:15]:
        vis  = "private" if repo.get("private") else "public"
        lang = repo.get("language") or "—"
        stars = repo.get("stargazers_count", 0)
        lines.append(f"  {repo['name']}  ({vis}, {lang}, ⭐{stars})")
    return "\n".join(lines)


def _get_profile(_args: dict) -> str:
    data = get_github_profile()
    if "message" in data:
        return f"Failed to fetch profile: {data['message']}"
    return (
        f"Username     : {data.get('login')}\n"
        f"Name         : {data.get('name')}\n"
        f"Followers    : {data.get('followers')}\n"
        f"Following    : {data.get('following')}\n"
        f"Public Repos : {data.get('public_repos')}\n"
        f"Location     : {data.get('location')}\n"
        f"URL          : {data.get('html_url')}"
    )


def _get_repositories(args: dict) -> str:
    limit = min(int(args.get("limit", 20)), 30)
    repos = fetch_repositories(limit)
    if not repos:
        return "No repositories found (or failed to fetch)."
    lines = [f"Repositories ({len(repos)}):"]
    for r in repos:
        vis  = "private" if r.get("private") else "public"
        lang = r.get("language") or "—"
        stars = r.get("stargazers_count", 0)
        lines.append(f"  {r['name']}  ({vis}, {lang}, ⭐{stars})")
    return "\n".join(lines)


def _publish_project(args: dict) -> str:
    project_path = os.path.abspath(args["project_path"])
    if not os.path.isdir(project_path):
        return f"Project folder not found: {project_path}"

    repo_name   = args["repo_name"]
    description = args.get("description", "")
    private     = args.get("private", False)
    commit_msg  = args.get("commit_message", "Initial commit")
    username    = get_github_username()

    # Step 1: Create GitHub repository
    resp = repo_create(repo_name, description, private)
    if resp.status_code != 201:
        return f"Failed to create repository: {resp.json().get('message', 'Unknown error')}"
    html_url   = resp.json()["html_url"]
    remote_url = f"https://{username}@github.com/{username}/{repo_name}.git"

    # Step 2: Full git workflow
    git_init(project_path)
    git_add(project_path)
    git_commit(project_path, commit_msg)
    git_branch(project_path, "main")
    git_remote_add(project_path, remote_url)
    git_push(project_path)

    return (
        f"Project published successfully!\n"
        f"  Repository : {html_url}\n"
        f"  Branch     : main\n"
        f"  Commit     : '{commit_msg}'"
    )


def _generate_readme(args: dict) -> str:
    output_folder = args.get("output_folder", ".")
    os.makedirs(output_folder, exist_ok=True)
    data = {
        "name":         args.get("project_name", "Project"),
        "description":  args.get("description", ""),
        "features":     args.get("features", []),
        "installation": args.get("installation", ""),
        "usage":        args.get("usage", ""),
        "technologies": args.get("technologies", []),
        "license":      args.get("license", "MIT"),
        "author":       args.get("author", ""),
    }
    path = generate_readme(data, output_folder)
    return f"README.md generated at: {path}"


def _git_status(args: dict) -> str:
    path = args.get("path", ".")
    result = subprocess.run(
        ["git", "status"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.stdout or result.stderr or "No git output."


def _list_directory(args: dict) -> str:
    path = args.get("path", ".")
    try:
        entries = sorted(os.listdir(path))
        dirs    = [e + "/" for e in entries if os.path.isdir(os.path.join(path, e))]
        files   = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        return f"Directory: {os.path.abspath(path)}\n" + "\n".join(dirs + files)
    except Exception as exc:
        return f"Error listing directory: {exc}"


def _read_file(args: dict) -> str:
    file_path = args["path"]
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read(8000)  # Cap at 8 KB to avoid token overflow
        return f"--- {file_path} ---\n{content}"
    except Exception as exc:
        return f"Error reading file: {exc}"


# ── Dispatch table ─────────────────────────────────────────────────────────────

_DISPATCH: dict[str, callable] = {
    "create_repository":  _create_repository,
    "delete_repository":  _delete_repository,
    "rename_repository":  _rename_repository,
    "search_repositories":_search_repositories,
    "get_profile":        _get_profile,
    "get_repositories":   _get_repositories,
    "publish_project":    _publish_project,
    "generate_readme":    _generate_readme,
    "git_status":         _git_status,
    "list_directory":     _list_directory,
    "read_file":          _read_file,
}
