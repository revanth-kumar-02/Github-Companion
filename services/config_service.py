import json

def get_github_username():
    with open("config/settings.json","r") as file:
        settings = json.load(file)
    return settings["github_username"]