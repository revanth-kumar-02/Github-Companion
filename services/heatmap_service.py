import requests
from services.config_service import (
    get_github_username,
    get_github_token,
)
from utils.constants import GITHUB_API

def get_contribution_calendar():
    headers = {
        "Authorization": f"Bearer {get_github_token()}",
        "Content-Type": "application/json",
    }

    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """

    variables = {
        "username": get_github_username()
    }

    response = requests.post(
        f"{GITHUB_API}/graphql",
        json={
            "query": query,
            "variables": variables,
        },
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()