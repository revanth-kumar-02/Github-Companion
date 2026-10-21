"""System service for managing OS-level actions with timeouts and secure process execution."""
from __future__ import annotations
import os
import platform
import subprocess
import sys


def open_directory(path: str) -> None:
    """Open a directory in the default OS file explorer."""
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def launch_vscode(project_path: str) -> None:
    """Launch VS Code for the specified project path."""
    try:
        subprocess.Popen(["code", project_path])
    except Exception:
        # Fallback if code command is a shell script or batch on Windows
        subprocess.Popen(f'code "{project_path}"', shell=True)


def run_project_file(project_path: str, entry_file: str) -> None:
    """Launch python or JS entry point in a separate window or terminal."""
    if entry_file.endswith(".py"):
        if platform.system() == "Windows":
            py_path = f'"{sys.executable}"'
            subprocess.Popen(["start", "cmd", "/k", f'{py_path} "{entry_file}"'], cwd=project_path, shell=True)
        else:
            subprocess.Popen([sys.executable, entry_file], cwd=project_path)
    elif entry_file.endswith(".js"):
        if platform.system() == "Windows":
            subprocess.Popen(["start", "cmd", "/k", f'node "{entry_file}"'], cwd=project_path, shell=True)
        else:
            subprocess.Popen(["node", entry_file], cwd=project_path)


def compile_python_file(file_path: str, timeout: int = 15) -> subprocess.CompletedProcess:
    """Run py_compile on a python file to check for syntax/compilation issues."""
    return subprocess.run(
        [sys.executable, "-m", "py_compile", file_path],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_test_or_build(
    cmd: list[str] | str,
    cwd: str,
    timeout: int = 60,
    shell: bool = False,
) -> subprocess.CompletedProcess:
    """Run a test runner or builder command with an enforced timeout."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=shell, timeout=timeout)
