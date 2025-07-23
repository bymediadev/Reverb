import feedparser


def fetch_latest_episodes(rss_url, max_entries=10):
    feed = feedparser.parse(rss_url)
    episodes = []

    for entry in feed.entries[:max_entries]:
        title = entry.title
        published = entry.published
        summary = entry.get("summary", "")
        episodes.append({"title": title, "published": published, "summary": summary})

    return episodes
