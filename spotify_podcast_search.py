import os
import time
import json
import base64
import requests
from dotenv import load_dotenv
from openai import OpenAI
from openai.error import OpenAIError

CACHE_FILE = "podcast_cache.json"
MAX_RESULTS = 100  # max number of shows to fetch per keyword
PAGE_SIZE = 20     # Spotify max per page

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and OPENAI_API_KEY):
    raise EnvironmentError("Missing API keys in environment variables")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_spotify_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def fetch_podcasts(keyword, token):
    cache = load_cache()
    if keyword in cache:
        print(f"Using cached data for '{keyword}'")
        return cache[keyword]

    all_shows = []
    offset = 0

    while len(all_shows) < MAX_RESULTS:
        url = (
            f"https://api.spotify.com/v1/search?"
            f"q={keyword}&type=show&limit={PAGE_SIZE}&offset={offset}"
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        shows = data.get("shows", {}).get("items", [])
        if not shows:
            break

        all_shows.extend(shows)
        if len(shows) < PAGE_SIZE:
            break

        offset += PAGE_SIZE
        time.sleep(0.1)  # modest delay to avoid hitting rate limits

    # Save limited results in cache
    cache[keyword] = all_shows[:MAX_RESULTS]
    save_cache(cache)
    return cache[keyword]

def rank_podcasts_with_chatgpt(podcasts):
    ranked = []
    for show in podcasts:
        prompt = (
            f"Rate this podcast on a scale from 1 to 10 based on the title and description.\n\n"
            f"Title: {show.get('name', '')}\n"
            f"Description: {show.get('description', '')}\n\n"
            f"Score:"
        )

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a podcast ranking assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=5,
                temperature=0,
            )
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
        except (OpenAIError, ValueError):
            score = 0.0

        ranked.append({
            "id": show.get("id"),
            "name": show.get("name"),
            "description": show.get("description"),
            "publisher": show.get("publisher"),
            "score": score,
            "total_episodes": show.get("total_episodes"),
            "external_urls": show.get("external_urls", {}).get("spotify"),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked

def main():
    token = get_spotify_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

    keyword = input("Enter podcast search keyword: ").strip()
    podcasts = fetch_podcasts(keyword, token)
    print(f"Fetched {len(podcasts)} podcasts for keyword '{keyword}'")

    ranked = rank_podcasts_with_chatgpt(podcasts)
    print("\nTop 10 Ranked Podcasts:\n")
    for p in ranked[:10]:
        print(f"{p['score']:.1f} | {p['name']} (Episodes: {p['total_episodes']})")
        print(f"    {p['description'][:100]}...")
        print(f"    {p['external_urls']}\n")

    # Save full ranked list to JSON file
    output_file = f"ranked_podcasts_{keyword.replace(' ', '_')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(ranked, f, indent=2)

    print(f"Full ranked list saved to {output_file}")

if __name__ == "__main__":
    main()
