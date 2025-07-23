import requests
import base64
import os
import json
import time

CLIENT_ID = "your_id"
CLIENT_SECRET = "your_secret"
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def search_podcasts(token, query, limit=20, max_results=100):
    headers = {"Authorization": f"Bearer {token}"}
    all_results = []
    offset = 0

    while offset < max_results:
        url = f"https://api.spotify.com/v1/search?q={query}&type=show&limit={limit}&offset={offset}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        shows = data.get("shows", {}).get("items", [])
        if not shows:
            break
        all_results.extend(shows)
        offset += limit
        if len(shows) < limit:
            break
        time.sleep(0.5)  # simple rate limit
    return all_results

def cached_search(token, query, max_results=100):
    cache_file = os.path.join(CACHE_DIR, f"{query.replace(' ', '_')}.json")
    if os.path.exists(cache_file):
        print("Using cached results")
        with open(cache_file, "r") as f:
            return json.load(f)
    results = search_podcasts(token, query, max_results=max_results)
    with open(cache_file, "w") as f:
        json.dump(results, f, indent=2)
    return results

def rank_podcasts(podcasts):
    # Implement your AI ranking here. Dummy example:
    return sorted(podcasts, key=lambda p: p.get("popularity", 0), reverse=True)

def export_to_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    token = get_token(CLIENT_ID, CLIENT_SECRET)
    query = "business"
    podcasts = cached_search(token, query, max_results=100)
    ranked = rank_podcasts(podcasts)
    export_to_json(f"{query}_podcasts.json", ranked)
    print(f"Exported ranked podcasts to {query}_podcasts.json")
