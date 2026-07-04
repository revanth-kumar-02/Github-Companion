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
        ["git","log","-1"],
        capture_output=True,
        text=True,
    )
    return result.stdout


def git_init(project_folder):
    result = subprocess.run(
        ["git","init"],
        cwd=project_folder,
        capture_output=True,
        text=True,
    )
    return result.stdout

def git_add(project_folder):
    result = subprocess.run(
        ["git", "add", "."],
        cwd=project_folder,
        capture_output=True,
        text=True,
    )
    return result.stdout

def git_commit(project_path,message):
    result = subprocess.run(
        ["git","commit","-m",message],
        cwd=project_path,
        capture_output=True,
        text=True,
    )
    return result.stdout


def git_remote_add(project_path,remote_url):
    result = subprocess.run(
        ["git","remote","add","origin",remote_url],
        cwd=project_path,
        capture_output=True,
        text=True,
    )
    return result.stdout

def git_push(project_path):
    result = subprocess.run(
        ["git","push","origin","main"],
        cwd=project_path,
        capture_output=True,
        text=True,
    )
    return result.stdout

def git_branch(project_path, branch):
    """Rename the current branch using -M (force rename)."""
    result = subprocess.run(
        ["git", "branch", "-M", branch],
        cwd=project_path,
        capture_output=True,
        text=True,
    )
    return result.stdout

def git_remote(project_path):   
    result = subprocess.run(
            ["git","remote","-v"],
            cwd=project_path,
            capture_output=True,
            text=True,
        )
        
    return result.stdout


def git_clone(clone_url: str, dest_path: str) -> subprocess.CompletedProcess:
    """Clone a remote repository to a local folder destination."""
    return subprocess.run(
        ["git", "clone", clone_url, dest_path],
        capture_output=True,
        text=True
    )


def git_log_oneline(project_path: str) -> str:
    """Get the latest commit in oneline format."""
    result = subprocess.run(
        ["git", "log", "-n", "1", "--oneline"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.stdout


def git_status_in_dir(project_path: str) -> str:
    """Get Git status in the context of a specific repository directory."""
    result = subprocess.run(
        ["git", "status"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.stdout or result.stderr


def git_undo(project_path: str) -> None:
    """Undo uncommitted local changes and untracked files/folders."""
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=project_path, capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=project_path, capture_output=True)

