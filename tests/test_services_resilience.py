"""Tests for timeouts, error handling, and exit code validation (SEC-06 & SEC-07)."""
import subprocess
from unittest.mock import patch, MagicMock
import pytest
import requests

from github_companion.services.git_service import (
    GitError,
    _run_git,
    git_init,
    git_push,
    git_commit,
    get_git_version,
)
from github_companion.services.github_service import (
    get_github_profile,
    fetch_repositories,
    repo_create,
    repo_delete,
)
from github_companion.services.system_service import compile_python_file, run_test_or_build


def test_git_subprocess_timeout_raises_git_error():
    """Ensure subprocess.TimeoutExpired is translated into GitError and not swallowed."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["git", "push"], timeout=60)):
        with pytest.raises(GitError) as exc_info:
            git_push("/dummy/path")
        assert "timed out after 60s" in str(exc_info.value)


def test_git_subprocess_failure_raises_git_error_with_stderr():
    """Ensure non-zero exit code raises GitError with stderr details (never claims success)."""
    mock_failed_process = MagicMock(
        returncode=128,
        stdout="",
        stderr="fatal: remote origin already exists."
    )
    with patch("subprocess.run", return_value=mock_failed_process):
        with pytest.raises(GitError) as exc_info:
            _run_git(["git", "remote", "add", "origin", "url"], check=True)
        assert "remote origin already exists" in str(exc_info.value)


def test_git_commit_failure_never_returns_false_success():
    """Ensure git_commit raises GitError if commit fails (e.g. nothing to commit)."""
    mock_failed_process = MagicMock(
        returncode=1,
        stdout="",
        stderr="nothing to commit, working tree clean"
    )
    with patch("subprocess.run", return_value=mock_failed_process):
        with pytest.raises(GitError) as exc_info:
            git_commit("/dummy/path", "test commit")
        assert "nothing to commit" in str(exc_info.value)


def test_github_service_timeout_handled_gracefully():
    """Ensure network timeouts in GitHub service are caught and handled safely."""
    with patch("github_companion.services.github_service.get_github_username", return_value="testuser"), \
         patch("requests.get", side_effect=requests.Timeout("Connection timed out")):
        profile = get_github_profile()
        assert "message" in profile
        assert "error" in profile["message"].lower() or "timed out" in profile["message"].lower()


def test_github_service_profile_uses_auth_token():
    """Ensure get_github_profile attaches Authorization header when token is present."""
    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"login": "testuser", "name": "Test User"}

    with patch("github_companion.services.github_service.get_github_username", return_value="testuser"), \
         patch("github_companion.services.github_service.get_github_token", return_value="ghp_MYTOKEN"), \
         patch("requests.get", return_value=mock_resp) as mock_get:
        profile = get_github_profile()
        assert profile["login"] == "testuser"
        call_headers = mock_get.call_args[1].get("headers", {})
        assert call_headers.get("Authorization") == "Bearer ghp_MYTOKEN"
        assert mock_get.call_args[1].get("timeout") == 10


def test_system_service_timeouts_enforced():
    """Ensure system service compile and test runners enforce timeouts."""
    with patch("subprocess.run") as mock_sub:
        compile_python_file("test.py", timeout=12)
        assert mock_sub.call_args[1].get("timeout") == 12

        run_test_or_build(["pytest"], cwd=".", timeout=45)
        assert mock_sub.call_args[1].get("timeout") == 45
