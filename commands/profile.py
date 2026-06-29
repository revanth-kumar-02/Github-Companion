from services.github_service import get_github_profile
from utils.ui import error
from rich import print

def show_gc_profile():
    profile = get_github_profile()
    if profile is None:
        error("Unable to fetch GitHub Profile")
    
    print()
    print("[bold bright_white]GitHub Profile[/bold bright_white]")
    print("[white]" + "─" * 47 + "[/white]")
    print("Username     :",profile["login"])
    print("Name         :",profile["name"])
    print("Followers    :",profile["followers"])
    print("Following    :",profile["following"])
    print("Public repos :",profile["public_repos"])
    print("Location     :",profile["location"])
    print("Website      :",profile["blog"])
    print("[white]" + "─" * 47 + "[/white]")
    
    
    
   