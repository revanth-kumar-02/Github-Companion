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

from github_companion.services.github_service import (
    repo_create,
    repo_delete,
    repo_rename,
    search_repositories,
    get_github_profile,
    fetch_repositories,
)
from github_companion.services.git_service import (
    git_init,
    git_add,
    git_commit,
    git_branch,
    git_remote_add,
    git_push,
    get_git_status,
)
from github_companion.services.readme_service import generate_readme
from github_companion.services.config_service import get_github_username
from github_companion.utils.security import (
    SecurityError,
    validate_safe_path,
    validate_safe_command,
    requires_human_approval,
    prompt_confirmation,
)


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
            "description": "Permanently delete an existing GitHub repository. Requires explicit human confirmation by typing repository name.",
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
                "Defaults to private repository. Requires explicit user confirmation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_path":   {"type": "string",  "description": "Path to the project folder inside the workspace"},
                    "repo_name":      {"type": "string",  "description": "Name for the new GitHub repository"},
                    "description":    {"type": "string",  "description": "Repository description"},
                    "private":        {"type": "boolean", "description": "True for private, False for public (default: True)"},
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
            "description": "List all files and subdirectories in a workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list within workspace (defaults to current directory)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text contents of a workspace file (capped at 8 KB). Blocked outside workspace or for sensitive files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read within workspace"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or create a file within the workspace (creates directories automatically). Blocked outside workspace or for sensitive files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to write within workspace"},
                    "content": {"type": "string", "description": "Full content to write to the file"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute an allowlisted developer tool command locally (git, python, pytest, npm, cargo). Shell chaining is forbidden; modifying commands require user approval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command string to execute (e.g. 'pytest', 'git status')"},
                },
                "required": ["command"],
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
    repo_name = args.get("repo_name", "").strip()
    if not repo_name:
        return "Repository deletion failed: repo_name is required."

    confirm_prompt = (
        f"\n[DANGER] AI requested permanent deletion of GitHub repository '{repo_name}'.\n"
        f"To confirm, type the exact repository name '{repo_name}': "
    )
    if not prompt_confirmation(confirm_prompt, expected_match=repo_name):
        return f"Repository deletion cancelled: Confirmation mismatched or rejected by user."

    resp = repo_delete(repo_name)
    if resp.status_code == 204:
        return f"Repository '{repo_name}' deleted successfully."
    err = "Unknown error"
    try:
        err = resp.json().get("message", "Unknown error")
    except Exception:
        pass
    return f"Failed to delete repository: {err}"


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
    raw_path = args.get("project_path", "")
    try:
        safe_path = validate_safe_path(raw_path)
    except (SecurityError, FileNotFoundError) as exc:
        return f"Publishing failed: {exc}"

    if not os.path.isdir(safe_path):
        return f"Project folder not found or not a directory: {safe_path}"

    repo_name = args.get("repo_name", "").strip()
    if not repo_name:
        return "Publishing failed: repo_name is required."

    description = args.get("description", "")
    # Default to PRIVATE for safety
    private = args.get("private", True)
    commit_msg = args.get("commit_message", "Initial commit")
    username = get_github_username()
    if not username:
        return "Publishing failed: GitHub username is not configured."

    visibility_str = "Private" if private else "Public"
    confirm_prompt = (
        f"\nPublish local project '{safe_path}' to GitHub repository '{repo_name}'?\n"
        f"  Visibility : {visibility_str}\n"
        f"  Branch     : main\n"
        f"Confirm publish? (y/N): "
    )
    if not prompt_confirmation(confirm_prompt):
        return "Publishing cancelled: User confirmation was not granted."

    # Step 1: Create GitHub repository
    resp = repo_create(repo_name, description, private)
    if resp.status_code != 201:
        err = "Unknown error"
        try:
            err = resp.json().get("message", "Unknown error")
        except Exception:
            pass
        return f"Failed to create repository: {err}"

    data = resp.json()
    html_url = data.get("html_url", f"https://github.com/{username}/{repo_name}")
    remote_url = f"https://{username}@github.com/{username}/{repo_name}.git"

    # Step 2: Git workflow with error detection
    try:
        git_init(str(safe_path))
        git_add(str(safe_path))
        git_commit(str(safe_path), commit_msg)
        git_branch(str(safe_path), "main")
        git_remote_add(str(safe_path), remote_url)
        git_push(str(safe_path))
    except Exception as exc:
        return f"Repository created ({html_url}) but Git push workflow encountered an error: {exc}"

    return (
        f"Project published successfully!\n"
        f"  Repository : {html_url}\n"
        f"  Visibility : {visibility_str}\n"
        f"  Branch     : main\n"
        f"  Commit     : '{commit_msg}'"
    )


def _generate_readme(args: dict) -> str:
    output_folder = args.get("output_folder", ".")
    try:
        safe_folder = validate_safe_path(output_folder, allow_create=True)
    except SecurityError as exc:
        return f"README generation failed: {exc}"

    os.makedirs(safe_folder, exist_ok=True)
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
    path = generate_readme(data, str(safe_folder))
    return f"README.md generated at: {path}"


def _git_status(args: dict) -> str:
    path = args.get("path", ".")
    try:
        safe_path = validate_safe_path(path)
    except SecurityError as exc:
        return f"Security check failed: {exc}"

    result = subprocess.run(
        ["git", "status"],
        cwd=str(safe_path),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout or result.stderr or "No git output."


def _list_directory(args: dict) -> str:
    path = args.get("path", ".")
    try:
        safe_path = validate_safe_path(path)
        entries = sorted(os.listdir(safe_path))
        dirs    = [e + "/" for e in entries if os.path.isdir(os.path.join(safe_path, e))]
        files   = [e for e in entries if os.path.isfile(os.path.join(safe_path, e))]
        return f"Directory: {safe_path}\n" + "\n".join(dirs + files)
    except Exception as exc:
        return f"Error listing directory: {exc}"


def _read_file(args: dict) -> str:
    file_path = args.get("path", "")
    try:
        safe_path = validate_safe_path(file_path)
        with open(safe_path, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read(8000)  # Cap at 8 KB to avoid token overflow
        return f"--- {safe_path} ---\n{content}"
    except SecurityError as exc:
        return f"Security check failed: {exc}"
    except Exception as exc:
        return f"Error reading file: {exc}"


def _write_file(args: dict) -> str:
    path = args.get("path", "")
    content = args.get("content", "")
    try:
        safe_path = validate_safe_path(path, allow_create=True)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} characters to '{safe_path}'"
    except SecurityError as exc:
        return f"Security check failed: {exc}"
    except Exception as exc:
        return f"Error writing file: {exc}"


def _execute_command(args: dict) -> str:
    cmd = args.get("command", "")
    is_safe, reason, argv = validate_safe_command(cmd)
    if not is_safe or not argv:
        return f"Security check failed: {reason}"

    needs_approval, approval_reason = requires_human_approval(argv)
    if needs_approval:
        confirm_prompt = (
            f"\n[SECURITY] AI requested command that modifies state: '{cmd}'\n"
            f"Reason: {approval_reason}\n"
            f"Allow execution? (y/N): "
        )
        if not prompt_confirmation(confirm_prompt):
            return f"Execution rejected: User denied approval for command '{cmd}'."

    try:
        result = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = f"Exit code: {result.returncode}\n"
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        return output
    except subprocess.TimeoutExpired:
        return "Error executing command: Command timed out after 30 seconds."
    except Exception as exc:
        return f"Error executing command: {exc}"


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
    "write_file":         _write_file,
    "execute_command":    _execute_command,
}

