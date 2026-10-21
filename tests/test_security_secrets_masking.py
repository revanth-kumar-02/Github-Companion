"""Tests for secret scrubbing, masking, and permissions (SEC-05)."""
import os
import io
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from github_companion.utils.security import mask_secret
from github_companion.services.config_service import save_settings, ensure_gc_directories, _load, run_startup_diagnostics
from github_companion.commands.config import _display_config


def test_mask_secret_full_mask():
    """Ensure mask_secret does not leak prefix or token lengths."""
    tokens = [
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        "sk-or-v1-abcdef1234567890abcdef1234567890",
        "nvapi-999999999999",
        "short",
    ]
    for tok in tokens:
        masked = mask_secret(tok)
        assert tok not in masked
        assert tok[:6] not in masked
        assert tok[:8] not in masked
        assert "••••" in masked

    assert mask_secret("") == "Not Set"
    assert mask_secret(None) == "Not Set"


def test_config_display_masks_tokens(capsys):
    """Ensure _display_config masks all sensitive tokens."""
    mock_settings = {
        "github_username": "devuser",
        "github_token": "ghp_SECRETTOKEN123456789",
        "openrouter_api_key": "sk-or-v1-SECRET999",
        "nvidia_api_key": "nvapi-SECRETKEY111",
        "provider": "openrouter",
    }
    with patch("github_companion.commands.config._load", return_value=mock_settings):
        _display_config()
        captured = capsys.readouterr().out
        assert "ghp_SECRETTOKEN" not in captured
        assert "sk-or-v1-SECRET" not in captured
        assert "nvapi-SECRET" not in captured
        assert "••••" in captured


def test_startup_diagnostics_does_not_leak_key_fragments(capsys):
    """Ensure startup diagnostics never print key fragments or lengths."""
    with patch.dict(os.environ, {"GC_DEBUG": "true"}), \
         patch("github_companion.services.config_service.CONFIG_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_settings = {
            "github_token": "ghp_SECRETTOKEN123456789",
            "openrouter_api_key": "sk-or-v1-TOPSECRETKEY",
            "nvidia_api_key": "nvapi-SECRETKEY",
        }
        with patch("builtins.open", MagicMock()), \
             patch("json.load", return_value=mock_settings), \
             patch("os.path.getmtime", return_value=1700000000):
            run_startup_diagnostics()
            captured = capsys.readouterr().out
            assert "sk-or-v1" not in captured
            assert "TOPSECRETKEY" not in captured
            assert "SECRETTOKEN" not in captured
            # Should show boolean configured status
            assert "configured: True" in captured or "configured: true" in captured.lower()


def test_posix_file_permissions(tmp_path, monkeypatch):
    """Ensure on POSIX systems, config files and directories receive 0o700/0o600 permissions."""
    gc_dir = tmp_path / ".gc"
    config_file = gc_dir / "config.json"

    monkeypatch.setattr("github_companion.services.config_service.GC_DIR", gc_dir)
    monkeypatch.setattr("github_companion.services.config_service.CONFIG_PATH", config_file)

    if os.name != "nt":
        ensure_gc_directories()
        assert (gc_dir.stat().st_mode & 0o777) == 0o700

        save_settings({"theme": "default"})
        assert (config_file.stat().st_mode & 0o777) == 0o600
    else:
        # On Windows, ensure directories and files are successfully created without error
        ensure_gc_directories()
        assert gc_dir.exists()
        save_settings({"theme": "default"})
        assert config_file.exists()
