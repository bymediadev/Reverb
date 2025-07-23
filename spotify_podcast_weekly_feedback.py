import os
import requests
import base64
import time
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# OpenAI setup
openai_client = OpenAI()

TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"
SHOW_EPISODES_URL = "https://api.spotify.com/v1/shows/{show_id}/episodes"

CACHE_FILE = "spotify_cache.json"
CACHE_TTL = 3600 * 24 * 3  # 3 days cache for token and shows

def get_spotify_token(client_id, client_secret):
    """Get or refresh Spotify access token."""
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def search_podcasts(query, token, limit=50, max_results=150):
    """Search podcasts by keyword with pagination, only shows."""
    shows = []
    offset = 0

    while len(shows) < max_results:
        params = {
            "q": query,
            "type": "show",
            "limit": min(limit, max_results - len(shows)),
            "offset": offset,
        }
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("shows", {}).get("items", [])
        if not items:
            break
        shows.extend(items)
        if len(items) < params["limit"]:
            break
        offset += len(items)
        time.sleep(0.2)  # throttle to avoid rate limits

    return shows

def get_show_episodes(show_id, token, limit=5):
    """Fetch limited episodes for a show."""
    url = SHOW_EPISODES_URL.format(show_id=show_id)
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": limit}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json().get("items", [])

def ai_evaluate_text(openai_client, system_msg, user_prompt, max_tokens=150):
    """Generic AI evaluation call."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI evaluation error: {str(e)}"

def rank_and_feedback_episodes(openai_client, episodes):
    ranked_eps = []
    for ep in episodes:
        prompt = (
            f"Evaluate this podcast episode briefly:\n"
            f"- What makes it interesting or unique\n"
            f"- Its key topics or appeal\n"
            f"- Any weaknesses or missing info\n"
            f"- A relevance score from 1 to 10\n\n"
            f"Episode Title: {ep.get('name','')}\n"
            f"Episode Description: {ep.get('description','')}\n\n"
            f"Your evaluation:"
        )
        evaluation = ai_evaluate_text(
            openai_client,
            system_msg="You are a podcast episode evaluation assistant.",
            user_prompt=prompt,
        )
        ranked_eps.append({
            "id": ep.get("id"),
            "name": ep.get("name"),
            "description": ep.get("description"),
            "release_date": ep.get("release_date"),
            "evaluation": evaluation,
            "external_url": ep.get("external_urls", {}).get("spotify"),
        })
    return ranked_eps

def rank_and_feedback_shows_with_episodes(openai_client, shows, token, episodes_per_show=5):
    ranked = []
    for show in shows:
        episodes = get_show_episodes(show["id"], token, limit=episodes_per_show)
        ranked_episodes = rank_and_feedback_episodes(openai_client, episodes)

        prompt_show = (
            f"Evaluate this podcast show briefly:\n"
            f"- What makes it interesting or unique\n"
            f"- Its target audience\n"
            f"- Any weaknesses or missing info\n"
            f"- A relevance score from 1 to 10\n\n"
            f"Show Title: {show.get('name','')}\n"
            f"Show Description: {show.get('description','')}\n\n"
            f"Your evaluation:"
        )
        evaluation_show = ai_evaluate_text(
            openai_client,
            system_msg="You are a podcast show evaluation assistant.",
            user_prompt=prompt_show,
        )

        ranked.append({
            "id": show.get("id"),
            "name": show.get("name"),
            "description": show.get("description"),
            "publisher": show.get("publisher"),
            "total_episodes": show.get("total_episodes"),
            "external_url": show.get("external_urls", {}).get("spotify"),
            "evaluation": evaluation_show,
            "episodes": ranked_episodes,
        })
        time.sleep(0.3)  # throttle
    return ranked

def save_json(data, filename="podcast_feedback.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Getting Spotify token...")
    token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)

    keywords = ["business", "true crime", "comedy", "news", "sports"]
    all_ranked = {}

    for kw in keywords:
        print(f"Searching podcasts for keyword: '{kw}'")
        shows = search_podcasts(kw, token)
        print(f"Found {len(shows)} shows for '{kw}'")

        ranked = rank_and_feedback_shows_with_episodes(openai_client, shows, token)
        all_ranked[kw] = ranked

    save_json(all_ranked)
    print("Done! Results saved to podcast_feedback.json")

if __name__ == "__main__":
    main()
