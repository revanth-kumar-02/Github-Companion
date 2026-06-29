from services.config_service import get_github_username
from utils.constants import GITHUB_API
import requests

def get_github_profile():
    username = get_github_username()
    response = requests.get(f"{GITHUB_API}/users/{username}")

    
    
    return response.json()
    
    