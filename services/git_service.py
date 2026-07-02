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
