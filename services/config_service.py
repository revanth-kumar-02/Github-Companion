import json
from config import settings

def get_github_username():
    with open("config/setting.json","r") as file:
        settings = json.load(file)
    return settings["github_username"]