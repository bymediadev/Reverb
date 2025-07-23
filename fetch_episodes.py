import os
import base64
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

def get_token(client_id, client_secret):
    """
    Request an access token from Spotify using Client Credentials flow.
    """
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token']

def get_show_episodes(show_id, token, limit=50):
    """
    Fetch up to `limit` episodes of a Spotify show by its ID.
    """
    url = f"https://api.spotify.com/v1/shows/{show_id}/episodes?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def list_categories(token):
    """
    Print available Spotify browse categories (mostly music).
    """
    url = "https://api.spotify.com/v1/browse/categories?limit=50"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    categories = response.json()["categories"]["items"]
    
    print("\nAvailable Spotify Categories:\n")
    for cat in categories:
        print(f"- {cat['name']} (ID: {cat['id']})")

if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: Spotify client ID or secret not found in environment variables.")
        exit(1)
    
    token = get_token(CLIENT_ID, CLIENT_SECRET)
    
    # Optional: List categories (mostly music, podcast categories aren't exposed)
    list_categories(token)
    
    # Replace with your show ID (example provided)
    show_id = "1aWHCFDYVhoZSAOxt1vcaa"
    
    print(f"\nFetching episodes for show ID: {show_id}\n")
    episodes_data = get_show_episodes(show_id, token)
    
    for ep in episodes_data['items']:
        print(f"Episode: {ep['name']} - Release Date: {ep['release_date']}")
