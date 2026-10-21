"""Tests for CLI flags, version display, and unconfigured environments (CLI-01 & CLI-02)."""
import sys
from unittest.mock import patch
import pytest

from github_companion.app import main
from github_companion.commands.version import show_gc_version
from github_companion import __version__


def test_version_command_output(capsys):
    """Ensure show_gc_version displays both GitHub Companion and Git CLI versions."""
    with patch("github_companion.commands.version.get_git_version", return_value="git version 2.45.0"):
        show_gc_version()
        captured = capsys.readouterr().out
        assert f"v{__version__}" in captured
        assert "git version 2.45.0" in captured


def test_main_version_flags_bypass_setup_wizard(capsys):
    """Ensure --version and -v run immediately without requiring config or triggering setup wizard."""
    for flag in ["--version", "-v", "version"]:
        with patch.object(sys, "argv", ["gc", flag]), \
             patch("github_companion.services.config_service.is_configured", return_value=False), \
             patch("github_companion.services.setup_wizard.run_setup_wizard") as mock_wizard:
            main()
            captured = capsys.readouterr().out
            assert f"v{__version__}" in captured
            mock_wizard.assert_not_called()


def test_main_help_flags_bypass_setup_wizard(capsys):
    """Ensure --help and -h run immediately without triggering setup wizard."""
    for flag in ["--help", "-h", "help"]:
        with patch.object(sys, "argv", ["gc", flag]), \
             patch("github_companion.services.config_service.is_configured", return_value=False), \
             patch("github_companion.services.setup_wizard.run_setup_wizard") as mock_wizard:
            main()
            captured = capsys.readouterr().out
            assert "Available Commands" in captured
            mock_wizard.assert_not_called()


def test_unconfigured_non_interactive_exits_safely():
    """Ensure unconfigured execution in non-interactive environment exits with code 1 instead of hanging."""
    with patch.object(sys, "argv", ["gc"]), \
         patch("github_companion.services.config_service.is_configured", return_value=False), \
         patch("sys.stdin.isatty", return_value=False), \
         pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
