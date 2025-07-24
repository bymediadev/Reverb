import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("Missing Spotify client credentials. Check your .env file.")

def get_access_token():
    auth_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}

    response = requests.post(auth_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def fetch_spotify_podcasts(query="podcast", limit=5):
    token = get_access_token()
    search_url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "q": query,
        "type": "show",
        "limit": limit
    }

    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    shows = response.json().get("shows", {}).get("items", [])
    
    results = []
    for show in shows:
        results.append({
            "name": show["name"],
            "publisher": show["publisher"],
            "description": show["description"],
            "id": show["id"],
            "uri": show["uri"],
            "total_episodes": show.get("total_episodes", "N/A"),
            "languages": show.get("languages", [])
        })
    return results

if __name__ == "__main__":
    podcasts = fetch_spotify_podcasts("technology", 3)
    for p in podcasts:
        print(f"{p['name']} by {p['publisher']} ({p['total_episodes']} episodes)")
