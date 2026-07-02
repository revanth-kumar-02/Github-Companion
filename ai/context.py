"""Project context collector for the GitHub Companion AI agent."""
from __future__ import annotations
import os
import subprocess


def get_project_context() -> dict:
    """
    Gather the current project's context to inject into AI prompts.

    Returns a dict with:
        cwd          - current working directory
        files        - top-level file/folder names
        git_branch   - current git branch (or empty string)
        git_status   - short git status output (or empty string)
        detected     - list of detected project-type labels
    """
    return {
        "cwd":        os.getcwd(),
        "files":      _list_top_level(),
        "git_branch": _get_git_branch(),
        "git_status": _get_git_status_short(),
        "detected":   _detect_project_type(),
    }


def format_context(context: dict) -> str:
    """Format context dict into a compact, readable string for the system prompt."""
    detected = ", ".join(context["detected"]) or "unknown"
    files    = ", ".join(context["files"][:20]) or "none"
    branch   = context["git_branch"] or "not a git repo"

    lines = [
        f"Working Directory : {context['cwd']}",
        f"Git Branch        : {branch}",
        f"Project Type      : {detected}",
        f"Top-Level Files   : {files}",
    ]
    if context["git_status"]:
        # Limit to first 10 lines to avoid flooding the prompt
        status_lines = context["git_status"].splitlines()[:10]
        lines.append("Git Status        :\n  " + "\n  ".join(status_lines))

    return "\n".join(lines)


# ── Private helpers ────────────────────────────────────────────────────────────

def _list_top_level() -> list[str]:
    try:
        return sorted(os.listdir("."))
    except Exception:
        return []


def _get_git_status_short() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _get_git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _detect_project_type() -> list[str]:
    """Heuristically identify the project type from common marker files."""
    markers = {
        "requirements.txt":  "Python",
        "pyproject.toml":    "Python (pyproject)",
        "package.json":      "Node.js",
        "Cargo.toml":        "Rust",
        "go.mod":            "Go",
        "pom.xml":           "Java/Maven",
        "build.gradle":      "Java/Gradle",
        "Dockerfile":        "Docker",
        "docker-compose.yml":"Docker Compose",
        "README.md":         "README present",
        ".env":              "Env file present",
    }
    return [label for filename, label in markers.items() if os.path.exists(filename)]
