"""Local Git repository service."""
import subprocess


def get_git_version():
    result = subprocess.run(
        ["git", "--version"],
        capture_output=True,
        text=True
    )
    
    return result.stdout

def get_git_status():
    result = subprocess.run(
        ["git","status"],
        capture_output=True,
        text=True,
    )
    return result.stdout

def get_latest_commit():
    result = subprocess.run(
        ["git","log -1"],
        capture_output=True,
        text=True,
    )
    return result.stdout


