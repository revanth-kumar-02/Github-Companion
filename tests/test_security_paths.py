"""Tests for path canonicalization, workspace jail, and sensitive file protection (SEC-03)."""
import os
import tempfile
from pathlib import Path
import pytest

from github_companion.utils.security import (
    validate_safe_path,
    is_sensitive_path,
    SecurityError,
)
from github_companion.ai.tools import execute_tool


@pytest.fixture
def workspace_jail():
    """Create a temporary workspace directory for testing jail enforcement."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir).resolve()
        # Create normal files
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
        (root / "README.md").write_text("# Test", encoding="utf-8")

        # Create forbidden sensitive files
        (root / ".env").write_text("SECRET=123", encoding="utf-8")
        (root / ".env.local").write_text("API_KEY=xyz", encoding="utf-8")
        (root / "id_rsa").write_text("PRIVATE KEY", encoding="utf-8")
        (root / "config.json").write_text("{}", encoding="utf-8")
        (root / "key.pem").write_text("CERT", encoding="utf-8")
        (root / ".ssh").mkdir()
        (root / ".ssh" / "id_ed25519").write_text("KEY", encoding="utf-8")

        yield root


def test_path_traversal_outside_workspace_blocked(workspace_jail):
    """Ensure ../../ traversal attempts raise SecurityError."""
    outside_attempts = [
        "../outside.txt",
        "../../outside.txt",
        "src/../../outside.txt",
        "..\\..\\outside.txt",
        "C:\\Windows\\System32\\cmd.exe",
        "/etc/passwd",
        "/etc/shadow",
    ]
    for attempt in outside_attempts:
        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path(attempt, workspace_root=workspace_jail)
        assert "outside the allowed workspace" in str(exc_info.value).lower()


def test_sensitive_files_blocked_within_workspace(workspace_jail):
    """Ensure sensitive files (.env, keys, config.json) cannot be accessed even inside workspace."""
    sensitive_targets = [
        ".env",
        ".env.local",
        "id_rsa",
        "config.json",
        "key.pem",
        ".ssh/id_ed25519",
    ]
    for target in sensitive_targets:
        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path(target, workspace_root=workspace_jail)
        assert "sensitive file" in str(exc_info.value).lower()


def test_valid_workspace_files_pass(workspace_jail):
    """Ensure normal project files inside the workspace are permitted."""
    valid_targets = [
        "README.md",
        "src/main.py",
        "src",
    ]
    for target in valid_targets:
        resolved = validate_safe_path(target, workspace_root=workspace_jail)
        assert resolved.exists()
        assert resolved.is_relative_to(workspace_jail)


def test_allow_create_mode_for_new_files(workspace_jail):
    """Ensure allow_create=True permits safe new files but blocks outside paths."""
    new_file = "src/new_module.py"
    resolved = validate_safe_path(new_file, workspace_root=workspace_jail, allow_create=True)
    assert resolved == (workspace_jail / "src" / "new_module.py").resolve()

    # Traversal in create mode must still raise SecurityError
    with pytest.raises(SecurityError):
        validate_safe_path("../outside.py", workspace_root=workspace_jail, allow_create=True)

    # Creating a sensitive file (.env) in create mode must be blocked
    with pytest.raises(SecurityError):
        validate_safe_path(".env", workspace_root=workspace_jail, allow_create=True)


def test_read_file_tool_security(workspace_jail, monkeypatch):
    """Verify execute_tool('read_file') enforces security boundary."""
    monkeypatch.setattr(
        "github_companion.utils.security.get_effective_workspace_root",
        lambda: workspace_jail,
    )

    # Legitimate read
    res_ok = execute_tool("read_file", {"path": "src/main.py"})
    assert "print('hello')" in res_ok

    # Traversal read attempt
    res_trav = execute_tool("read_file", {"path": "../../etc/passwd"})
    assert "Security check failed" in res_trav

    # Sensitive file read attempt (.env)
    res_env = execute_tool("read_file", {"path": ".env"})
    assert "Security check failed" in res_env


def test_write_file_tool_security(workspace_jail, monkeypatch):
    """Verify execute_tool('write_file') enforces security boundary."""
    monkeypatch.setattr(
        "github_companion.utils.security.get_effective_workspace_root",
        lambda: workspace_jail,
    )

    # Legitimate write
    res_ok = execute_tool("write_file", {"path": "src/generated.py", "content": "x = 42"})
    assert "Successfully wrote" in res_ok
    assert (workspace_jail / "src" / "generated.py").read_text(encoding="utf-8") == "x = 42"

    # Traversal write attempt
    res_trav = execute_tool("write_file", {"path": "../escaped.py", "content": "bad"})
    assert "Security check failed" in res_trav
    assert not (workspace_jail.parent / "escaped.py").exists()

    # Sensitive file overwrite attempt
    res_env = execute_tool("write_file", {"path": ".env", "content": "EXPOSED=1"})
    assert "Security check failed" in res_env
    assert (workspace_jail / ".env").read_text(encoding="utf-8") == "SECRET=123"


def test_symlink_attacks_blocked(workspace_jail, tmp_path):
    """Ensure symbolic links pointing outside workspace or to sensitive files are blocked."""
    outside_file = tmp_path / "outside_secret.txt"
    outside_file.write_text("SUPER_SECRET", encoding="utf-8")

    link_outside = workspace_jail / "symlink_outside.txt"
    try:
        os.symlink(outside_file, link_outside)
        has_symlink = True
    except (OSError, NotImplementedError):
        has_symlink = False

    if has_symlink:
        with pytest.raises(SecurityError) as exc_info:
            validate_safe_path("symlink_outside.txt", workspace_root=workspace_jail)
        assert "outside the allowed workspace" in str(exc_info.value).lower()

        link_env = workspace_jail / "symlink_env.txt"
        try:
            os.symlink(workspace_jail / ".env", link_env)
            with pytest.raises(SecurityError) as exc_info2:
                validate_safe_path("symlink_env.txt", workspace_root=workspace_jail)
            assert "sensitive file" in str(exc_info2.value).lower()
        except (OSError, NotImplementedError):
            pass


def test_malformed_and_null_byte_paths_blocked(workspace_jail):
    """Ensure paths with null bytes or malformed characters raise SecurityError."""
    with pytest.raises(SecurityError):
        validate_safe_path("main.py\x00extra", workspace_root=workspace_jail)

