"""Security utilities for GitHub Companion — path validation, command allowlisting, secret masking, and confirmations."""
from __future__ import annotations
import os
import re
import shlex
import sys
from pathlib import Path


class SecurityError(Exception):
    """Raised when an operation violates security policy or boundaries."""
    pass


# ── Sensitive File & Directory Patterns ────────────────────────────────────────

SENSITIVE_PATTERNS = (
    r"^\.env(\..+)?$",             # .env, .env.local, .env.prod, etc.
    r"^.*id_(rsa|dsa|ecdsa|ed25519).*$", # SSH private keys
    r"^.*\.(pem|key|pkcs12|pfx|p12|kdbx|keystore)$", # Certificates / keys
    r"^config\.json$",              # GC or other local config
    r"^settings\.json$",
    r"^credentials(\.json)?$",
    r"^authorized_keys$",
    r"^known_hosts$",
    r"^\.netrc$",
    r"^\.npmrc$",
    r"^\.pypirc$",
)

SENSITIVE_DIR_NAMES = {
    ".ssh",
    ".aws",
    ".gnupg",
    ".gc",
    ".git",
}

# Block system roots on POSIX and Windows
SYSTEM_ROOT_PREFIXES = (
    "/etc",
    "/var/log",
    "/var/lib",
    "/var/run",
    "/var/root",
    "/var/spool",
    "/usr",
    "/bin",
    "/sbin",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "/root",
    "c:\\windows",
    "c:\\program files",
    "c:\\program files (x86)",
)


def get_effective_workspace_root() -> Path:
    """Return canonical Path of the configured workspace or current working directory."""
    try:
        from github_companion.services.config_service import get_default_workspace
        ws = get_default_workspace()
        if ws and os.path.exists(ws):
            return Path(ws).resolve()
    except Exception:
        pass
    return Path.cwd().resolve()


def is_sensitive_path(path: Path) -> bool:
    """Check if the given canonical path targets a sensitive file, directory, or system location."""
    # Check parts of the path for forbidden directory names
    for part in path.parts:
        if part.lower() in SENSITIVE_DIR_NAMES:
            return True

    filename = path.name.lower()
    for pattern in SENSITIVE_PATTERNS:
        if re.match(pattern, filename, re.IGNORECASE):
            return True

    path_str = str(path).lower().replace("\\", "/")
    for prefix in SYSTEM_ROOT_PREFIXES:
        norm_prefix = prefix.lower().replace("\\", "/")
        if path_str == norm_prefix or path_str.startswith(norm_prefix + "/"):
            return True

    return False


def validate_safe_path(
    target_path: str | Path,
    workspace_root: str | Path | None = None,
    allow_create: bool = False,
) -> Path:
    """
    Validate that target_path is within the permitted workspace directory and does not target sensitive files.

    Args:
        target_path: Relative or absolute path to validate.
        workspace_root: The root boundary (defaults to effective workspace root).
        allow_create: If True, allows target_path to not yet exist (e.g. for write operations).

    Returns:
        Canonical, resolved Path object.

    Raises:
        SecurityError: If path traverses outside the workspace or touches sensitive files.
    """
    if not target_path or not str(target_path).strip():
        raise SecurityError("Path cannot be empty.")

    target_str = str(target_path).strip()

    # Normalize backslashes to forward slashes across all platforms
    normalized = target_str.replace("\\", "/")

    # Reject Windows drive-letter paths on POSIX systems (e.g. C:/Windows/...)
    if os.name != "nt" and re.match(r"^[a-zA-Z]:", normalized):
        raise SecurityError(
            f"Path traversal detected: '{target_path}' resolves outside the allowed workspace."
        )

    root = (Path(workspace_root) if workspace_root else get_effective_workspace_root()).resolve()

    try:
        raw_path = Path(normalized)
        if not raw_path.is_absolute():
            resolved_path = (root / raw_path).resolve()
        else:
            resolved_path = raw_path.resolve()
    except (ValueError, TypeError) as exc:
        raise SecurityError(f"Malformed path '{target_path}': {exc}")

    # Boundary check: resolved_path must be inside root
    try:
        resolved_path.relative_to(root)
    except ValueError:
        raise SecurityError(
            f"Path traversal detected: '{target_path}' resolves outside the allowed workspace '{root}'."
        )

    # Sensitive files and directories check
    if is_sensitive_path(resolved_path):
        raise SecurityError(
            f"Access to sensitive file or directory '{resolved_path.name}' is strictly blocked."
        )

    if not allow_create and not resolved_path.exists():
        raise FileNotFoundError(f"File not found: '{resolved_path}'")

    return resolved_path


# ── Command Security & Allowlist ───────────────────────────────────────────────

# Disallowed shell meta-characters and command injection primitives
DANGEROUS_SHELL_PATTERNS = [
    r"&&", r"\|\|", r";", r"\|", r">", r"<", r"`", r"\$\(", r"\n", r"\r"
]

# Explicitly allowed safe CLI tools for agent workflows
ALLOWED_BINARIES = {
    "git",
    "python",
    "python3",
    "py",
    "pytest",
    "pip",
    "npm",
    "node",
    "npx",
    "cargo",
    "go",
    "ruff",
    "black",
    "flake8",
    "mypy",
}

# Explicitly forbidden destructive binaries
BLOCKED_BINARIES = {
    "rm",
    "del",
    "erase",
    "rmdir",
    "rd",
    "format",
    "dd",
    "shutdown",
    "reboot",
    "curl",
    "wget",
    "nc",
    "netcat",
    "ncat",
    "powershell",
    "powershell.exe",
    "cmd",
    "cmd.exe",
    "bash",
    "sh",
    "zsh",
    "sudo",
    "su",
    "chmod",
    "chown",
    "attrib",
}

# Safe git subcommands that do not mutate repository state or history
SAFE_GIT_SUBCOMMANDS = {
    "status",
    "diff",
    "log",
    "branch",
    "show",
    "tag",
    "check-ignore",
    "--version",
    "rev-parse",
}


def validate_safe_command(command: str) -> tuple[bool, str, list[str] | None]:
    """
    Validate that a command string uses only allowed binaries, does not contain shell injection,
    and returns parsed argument list for execution without shell=True.

    Returns:
        (is_safe, reason, argv_list)
    """
    if not command or not command.strip():
        return False, "Command cannot be empty.", None

    clean_cmd = command.strip()

    # 1. Reject shell chaining, redirects, pipes, and subshell injection
    for pat in DANGEROUS_SHELL_PATTERNS:
        if re.search(pat, clean_cmd):
            return False, f"Command contains forbidden shell metacharacters or chaining ('{pat}').", None

    # 2. Parse arguments safely
    try:
        argv = shlex.split(clean_cmd, posix=(os.name != "nt"))
    except Exception as exc:
        return False, f"Failed to parse command arguments: {exc}", None

    if not argv:
        return False, "No command tokens found.", None

    binary = os.path.basename(argv[0]).lower()
    if binary.endswith(".exe"):
        binary = binary[:-4]

    # 3. Check blocked binaries
    if binary in BLOCKED_BINARIES:
        return False, f"Execution of dangerous binary '{binary}' is blocked.", None

    # 4. Check allowed binaries
    if binary not in ALLOWED_BINARIES:
        return False, f"Command '{binary}' is not in the permitted developer tools allowlist.", None

    return True, "Command is permitted.", argv


def requires_human_approval(argv: list[str]) -> tuple[bool, str]:
    """
    Determine if a permitted command alters state and requires human confirmation.
    """
    binary = os.path.basename(argv[0]).lower()
    if binary.endswith(".exe"):
        binary = binary[:-4]

    if binary == "git" and len(argv) > 1:
        subcmd = argv[1].lower()
        if subcmd not in SAFE_GIT_SUBCOMMANDS:
            return True, f"Git subcommand '{subcmd}' modifies repository state or remote references."
        if subcmd == "branch" and any(arg in argv[2:] for arg in ("-d", "-D", "-m", "-M", "--delete", "--move")):
            return True, "Git branch deletion or renaming modifies repository state."
        if subcmd == "tag" and any(arg in argv[2:] for arg in ("-d", "--delete")):
            return True, "Git tag deletion modifies repository state."

    if binary in ("pip", "npm") and len(argv) > 1:
        subcmd = argv[1].lower()
        if subcmd in ("install", "uninstall", "update", "remove", "i", "audit", "prune"):
            return True, "Package manager command modifies local dependencies."

    if binary in ("python", "python3", "py") and len(argv) > 1:
        if "-c" in argv:
            return True, "Execution of inline Python script (-c) can modify system state."
        if any(arg.endswith(".py") for arg in argv[1:]) and "-m" not in argv:
            return True, "Executing Python script can alter system or workspace state."

    if binary in ("node", "npx") and len(argv) > 1:
        if "-e" in argv:
            return True, "Execution of inline Node script (-e) can modify system state."

    return False, ""


# ── Confirmation & Non-Interactive Safety ──────────────────────────────────────

def is_interactive() -> bool:
    """Return True if running in an interactive terminal."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def prompt_confirmation(prompt_text: str, expected_match: str | None = None) -> bool:
    """
    Prompt for confirmation. In non-interactive mode, fails closed (returns False).
    If expected_match is provided, user must type the exact match.
    """
    if not is_interactive():
        # Reject dangerous operations in non-interactive mode unless explicitly allowed
        if os.environ.get("GC_ALLOW_AUTOMATED_ACTIONS") == "1":
            return True
        return False

    try:
        response = input(prompt_text).strip()
        if expected_match is not None:
            return response.strip() == expected_match.strip()
        return response.lower() in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        return False


# ── Secret Masking ─────────────────────────────────────────────────────────────

def mask_secret(secret: str | None, placeholder: str = "••••••••••••") -> str:
    """Mask a secret string completely without revealing key fragments or lengths."""
    if not secret:
        return "Not Set"
    return placeholder
