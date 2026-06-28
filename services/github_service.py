
import requests

def get_github_profile():
    response = requests.get("https://api.github.com/users/revanth-kumar-02")

    profile = response.json()
    
    return profile
    
    