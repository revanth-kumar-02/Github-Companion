"""Local Git repository service with timeouts, returncode validation, and safe error handling."""
from __future__ import annotations
import subprocess


class GitError(RuntimeError):
    """Raised when a Git command fails or times out."""
    pass


def _run_git(
    cmd: list[str],
    cwd: str | None = None,
    timeout: int = 15,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a git command with timeout and returncode validation."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if check and result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or f"Exited with code {result.returncode}"
            raise GitError(f"Git command {' '.join(cmd)} failed: {error_msg}")
        return result
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"Git command {' '.join(cmd)} timed out after {timeout}s.") from exc
    except FileNotFoundError as exc:
        raise GitError("Git executable not found in system PATH.") from exc


def get_git_version() -> str:
    """Return Git version string or empty string if not installed/error."""
    try:
        result = _run_git(["git", "--version"], timeout=5, check=True)
        return result.stdout.strip()
    except Exception:
        return ""


def get_git_status() -> str:
    """Return Git status of the current working directory."""
    try:
        result = _run_git(["git", "status"], timeout=10, check=False)
        return result.stdout or result.stderr
    except Exception as exc:
        return f"Failed to get git status: {exc}"


def get_latest_commit() -> str:
    """Return latest commit log message."""
    try:
        result = _run_git(["git", "log", "-1"], timeout=10, check=False)
        return result.stdout or result.stderr
    except Exception as exc:
        return f"Failed to get latest commit: {exc}"


def git_init(project_folder: str) -> str:
    """Initialize a new git repository in project_folder."""
    result = _run_git(["git", "init"], cwd=project_folder, timeout=15, check=True)
    return result.stdout.strip()


def git_add(project_folder: str) -> str:
    """Stage all changes in project_folder."""
    result = _run_git(["git", "add", "."], cwd=project_folder, timeout=30, check=True)
    return result.stdout.strip()


def git_commit(project_path: str, message: str) -> str:
    """Commit staged changes in project_path."""
    result = _run_git(["git", "commit", "-m", message], cwd=project_path, timeout=30, check=True)
    return result.stdout.strip()


def git_remote_add(project_path: str, remote_url: str) -> str:
    """Add origin remote to repository."""
    result = _run_git(
        ["git", "remote", "add", "origin", remote_url],
        cwd=project_path,
        timeout=15,
        check=True,
    )
    return result.stdout.strip()


def git_push(project_path: str) -> str:
    """Push main branch to origin."""
    result = _run_git(
        ["git", "push", "origin", "main"],
        cwd=project_path,
        timeout=60,
        check=True,
    )
    return result.stdout.strip()


def git_branch(project_path: str, branch: str) -> str:
    """Rename current branch using -M (force rename)."""
    result = _run_git(
        ["git", "branch", "-M", branch],
        cwd=project_path,
        timeout=15,
        check=True,
    )
    return result.stdout.strip()


def git_remote(project_path: str) -> str:
    """List remotes with verbose URLs."""
    result = _run_git(["git", "remote", "-v"], cwd=project_path, timeout=15, check=False)
    return result.stdout.strip()


def git_clone(clone_url: str, dest_path: str) -> subprocess.CompletedProcess:
    """Clone a remote repository to destination path."""
    return _run_git(["git", "clone", clone_url, dest_path], timeout=90, check=False)


def git_log_oneline(project_path: str) -> str:
    """Get the latest commit in oneline format."""
    result = _run_git(["git", "log", "-n", "1", "--oneline"], cwd=project_path, timeout=10, check=False)
    return result.stdout.strip()


def git_status_in_dir(project_path: str) -> str:
    """Get Git status in the context of a specific repository directory."""
    result = _run_git(["git", "status"], cwd=project_path, timeout=15, check=False)
    return result.stdout or result.stderr


def git_undo(project_path: str) -> None:
    """Undo uncommitted local changes and untracked files/folders."""
    _run_git(["git", "reset", "--hard", "HEAD"], cwd=project_path, timeout=15, check=False)
    _run_git(["git", "clean", "-fd"], cwd=project_path, timeout=15, check=False)
