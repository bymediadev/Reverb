import os
import time
import feedparser
from main import rank_episode  # Assuming your ranking logic is here
from utils import leaderboard_utils  # Adjust to your EchoBoard module paths

RSS_URL = "https://anchor.fm/s/7ae43ac/podcast/rss"
SEEN_EPISODES_FILE = "data/seen_episodes.txt"


def load_seen_episodes():
    if not os.path.exists(SEEN_EPISODES_FILE):
        return set()
    with open(SEEN_EPISODES_FILE, "r") as f:
        return set(line.strip() for line in f)


def save_seen_episode(episode_id):
    with open(SEEN_EPISODES_FILE, "a") as f:
        f.write(f"{episode_id}\n")


def poll_feed():
    seen = load_seen_episodes()
    feed = feedparser.parse(RSS_URL)

    for entry in feed.entries:
        if entry.id not in seen:
            print(f"New episode detected: {entry.title}")
            # Use your EchoBoard logic to rank and update
            rank_episode(
                entry
            )  # Implement this in main.py or wherever ranking logic is
            save_seen_episode(entry.id)


if __name__ == "__main__":
    while True:
        poll_feed()
        time.sleep(3600)  # Run every hour
