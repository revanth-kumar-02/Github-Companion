import requests


profile = response.json()

print(profile["login"])
print(profile["name"])
print(profile["followers"])
print(profile["following"])
print(profile["public_repos"])
