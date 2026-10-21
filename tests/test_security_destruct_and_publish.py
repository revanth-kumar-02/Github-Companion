"""Tests for remote deletion confirmations and private publishing defaults (SEC-02 & SEC-04)."""
from unittest.mock import patch, MagicMock
import pytest

from github_companion.ai.tools import execute_tool
from github_companion.commands.delete import delete_repo
from github_companion.commands.publish import show_gc_publish


def test_ai_delete_repository_requires_exact_confirmation():
    """Ensure AI delete_repository tool requires typing the exact repo name."""
    with patch("github_companion.ai.tools.prompt_confirmation", return_value=False) as mock_prompt:
        res = execute_tool("delete_repository", {"repo_name": "critical-repo"})
        assert "cancelled" in res.lower()
        mock_prompt.assert_called_once()
        # Ensure exact match was requested
        assert mock_prompt.call_args[1].get("expected_match") == "critical-repo"


def test_ai_delete_repository_succeeds_when_confirmed():
    """Ensure delete_repository executes only when exact confirmation is given."""
    mock_resp = MagicMock(status_code=204)
    with patch("github_companion.ai.tools.prompt_confirmation", return_value=True), \
         patch("github_companion.ai.tools.repo_delete", return_value=mock_resp) as mock_delete:
        res = execute_tool("delete_repository", {"repo_name": "demo-repo"})
        assert "deleted successfully" in res
        mock_delete.assert_called_once_with("demo-repo")


def test_cli_delete_repo_requires_exact_name():
    """Ensure CLI delete_repo command prompts and checks exact name match."""
    with patch("rich.console.Console.input", return_value="my-prod-repo"), \
         patch("github_companion.commands.delete.prompt_confirmation", return_value=False) as mock_prompt, \
         patch("github_companion.commands.delete.repo_delete") as mock_delete:
        delete_repo()
        mock_prompt.assert_called_once()
        assert mock_prompt.call_args[1].get("expected_match") == "my-prod-repo"
        mock_delete.assert_not_called()


def test_ai_publish_project_defaults_to_private():
    """Ensure AI publish_project defaults to private=True."""
    mock_resp = MagicMock(status_code=201)
    mock_resp.json.return_value = {"html_url": "https://github.com/user/new-project"}

    with patch("github_companion.ai.tools.prompt_confirmation", return_value=True), \
         patch("github_companion.ai.tools.validate_safe_path", return_value="C:/workspace/my-proj"), \
         patch("os.path.isdir", return_value=True), \
         patch("github_companion.ai.tools.get_github_username", return_value="testuser"), \
         patch("github_companion.ai.tools.repo_create", return_value=mock_resp) as mock_create, \
         patch("github_companion.ai.tools.git_init"), \
         patch("github_companion.ai.tools.git_add"), \
         patch("github_companion.ai.tools.git_commit"), \
         patch("github_companion.ai.tools.git_branch"), \
         patch("github_companion.ai.tools.git_remote_add"), \
         patch("github_companion.ai.tools.git_push"):

        # Call without specifying private
        res = execute_tool("publish_project", {
            "project_path": "my-proj",
            "repo_name": "new-project"
        })
        assert "published successfully" in res
        # repo_create args: (repo_name, description, private)
        assert mock_create.call_args[0][2] is True, "Default visibility must be True (Private)"


def test_ai_publish_project_rejects_without_confirmation():
    """Ensure AI publish_project aborts if user denies confirmation."""
    with patch("github_companion.ai.tools.prompt_confirmation", return_value=False), \
         patch("github_companion.ai.tools.validate_safe_path", return_value="C:/workspace/my-proj"), \
         patch("os.path.isdir", return_value=True), \
         patch("github_companion.ai.tools.get_github_username", return_value="testuser"), \
         patch("github_companion.ai.tools.repo_create") as mock_create:
        res = execute_tool("publish_project", {
            "project_path": "my-proj",
            "repo_name": "new-project"
        })
        assert "cancelled" in res.lower()
        mock_create.assert_not_called()


def test_cli_publish_defaults_to_private():
    """Ensure CLI show_gc_publish defaults to private=True when user presses Enter."""
    mock_resp = MagicMock(status_code=201)
    mock_resp.json.return_value = {"html_url": "https://github.com/user/cli-project"}

    inputs = [
        "my-proj",  # folder
        "cli-repo", # repo name
        "desc",     # description
        "",         # Private Repository? Enter -> Default [Y] (private=True)
        "",         # Commit message -> Enter
    ]
    with patch("rich.console.Console.input", side_effect=inputs), \
         patch("github_companion.commands.publish.validate_safe_path", return_value="C:/workspace/my-proj"), \
         patch("os.path.isdir", return_value=True), \
         patch("github_companion.commands.publish.prompt_confirmation", return_value=True), \
         patch("github_companion.commands.publish.get_github_username", return_value="cliuser"), \
         patch("github_companion.commands.publish.repo_create", return_value=mock_resp) as mock_create, \
         patch("github_companion.commands.publish.git_init"), \
         patch("github_companion.commands.publish.git_add"), \
         patch("github_companion.commands.publish.git_commit"), \
         patch("github_companion.commands.publish.git_branch"), \
         patch("github_companion.commands.publish.git_remote_add"), \
         patch("github_companion.commands.publish.git_push"):

        show_gc_publish()
        assert mock_create.call_args[0][2] is True, "Default private setting must be True"


def test_cli_publish_cancels_on_rejected_confirmation():
    """Ensure CLI show_gc_publish aborts if confirmation prompt is declined."""
    inputs = [
        "my-proj",
        "cli-repo",
        "desc",
        "",
        "",
    ]
    with patch("rich.console.Console.input", side_effect=inputs), \
         patch("github_companion.commands.publish.validate_safe_path", return_value="C:/workspace/my-proj"), \
         patch("os.path.isdir", return_value=True), \
         patch("github_companion.commands.publish.prompt_confirmation", return_value=False), \
         patch("github_companion.commands.publish.repo_create") as mock_create:

        show_gc_publish()
        mock_create.assert_not_called()

