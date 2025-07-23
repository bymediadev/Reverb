import os
import json
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

PODCAST_KEYWORDS = ["podcast", "episode", "interview", "talk", "discussion", "show"]
OUTPUT_FILE = "youtube_podcast_sample.json"

def is_podcast_video(title, description):
    combined = f"{title} {description}".lower()
    return any(keyword in combined for keyword in PODCAST_KEYWORDS)

def search_youtube(query, max_results=10):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} podcast",
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": max_results
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["items"]

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception:
        return None

def get_comments(video_id, max_comments=5):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": YOUTUBE_API_KEY,
        "maxResults": max_comments,
        "textFormat": "plainText"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    comments_data = response.json().get("items", [])
    return [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for item in comments_data]

def fetch_podcast_context(query):
    results = search_youtube(query)
    context_data = []

    for vid in results:
        title = vid["snippet"]["title"]
        description = vid["snippet"]["description"]

        if not is_podcast_video(title, description):
            continue

        video_id = vid["id"]["videoId"]
        transcript = get_transcript(video_id)
        comments = get_comments(video_id)

        context_data.append({
            "video_id": video_id,
            "title": title,
            "description": description,
            "transcript": transcript or "(Transcript unavailable)",
            "comments": comments
        })

    return context_data

# Run and save
if __name__ == "__main__":
    keyword = "AI productivity"
    context = fetch_podcast_context(keyword)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved podcast data to {OUTPUT_FILE}")
