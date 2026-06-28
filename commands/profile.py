from services.github_service import get_github_profile

def show_gc_profile():
    profile = get_github_profile()

    print("GitHub Profile")
    print("════════════════════════════════════════════════════")
    print("Username     :",profile["login"])
    print("Name         :",profile["name"])
    print("Followers    :",profile["followers"])
    print("Following    :",profile["following"])
    print("Public repos :",profile["public_repos"])
    print("Location     :",profile["location"])
    print("Website      :",profile["blog"])
    print("════════════════════════════════════════════════════")
    
    
   