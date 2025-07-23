# podcast_feedback_api.py

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import openai
import os
import requests
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
SPOTIFY_TOKEN = os.getenv("SPOTIFY_TOKEN")  # You may want to automate refreshing this

app = FastAPI()

class FeedbackRequest(BaseModel):
    transcript: str
    comments: list[str]

class SearchRequest(BaseModel):
    keyword: str
    limit: int = 20

@app.get("/search")
def search_podcasts(keyword: str, limit: int = 20):
    headers = {"Authorization": f"Bearer {SPOTIFY_TOKEN}"}
    url = f"https://api.spotify.com/v1/search?q={keyword}&type=show&limit={limit}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Spotify search failed")
    return response.json()

@app.get("/episodes/{show_id}")
def get_episodes(show_id: str):
    headers = {"Authorization": f"Bearer {SPOTIFY_TOKEN}"}
    url = f"https://api.spotify.com/v1/shows/{show_id}/episodes?limit=50"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch episodes")
    return response.json()

@app.post("/feedback")
def generate_feedback(req: FeedbackRequest):
    comments_str = "\n".join(req.comments)
    prompt = f"""
You are an expert podcast coach.
Given the following podcast transcript and listener comments, give constructive, clear, helpful feedback with a coaching tone.
Focus on:
- Content quality
- Delivery & tone
- Engagement
- Structure
- Suggestions for improvement

Transcript:
{req.transcript}

Listener Comments:
{comments_str}

Respond with your feedback:
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional podcast coach."},
                {"role": "user", "content": prompt}
            ]
        )
        return {"feedback": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
