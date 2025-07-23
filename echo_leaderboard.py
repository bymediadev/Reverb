# echo_leaderboard.py
import feedparser
import json
import pandas as pd
import streamlit as st
from pathlib import Path
import os

# Set base directory
BASE_DIR = Path("C:/EchoBoard")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# File paths inside base directory
SCORES_JSON = BASE_DIR / "echo_scores.json"
LEADERBOARD_CSV = BASE_DIR / "leaderboard.csv"


def load_scores(json_path=SCORES_JSON):
    if not json_path.exists():
        st.warning(f"Score file {json_path} not found. Starting fresh.")
        return pd.DataFrame()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def parse_rss_feed(rss_url):
    feed = feedparser.parse(rss_url)
    episodes = []
    for entry in feed.entries:
        episodes.append(
            {
                "episode_id": entry.get("id") or entry.get("link"),
                "title": entry.get("title"),
                "published": entry.get("published"),
                "link": entry.get("link"),
                "duration": entry.get("itunes_duration", "unknown"),
            }
        )
    return pd.DataFrame(episodes)


def merge_data(episodes_df, scores_df):
    if scores_df.empty:
        episodes_df["score"] = None
        episodes_df["improvement"] = None
    else:
        merged = episodes_df.merge(scores_df, how="left", on="episode_id")
        episodes_df = merged
    return episodes_df


def normalize_scores(df, score_col="score"):
    if df[score_col].isnull().all():
        df["norm_score"] = 0
    else:
        min_score = df[score_col].min()
        max_score = df[score_col].max()
        range_score = max_score - min_score or 1
        df["norm_score"] = ((df[score_col] - min_score) / range_score * 100).fillna(0)
    return df


def assign_badges(row):
    badges = []
    if row["norm_score"] >= 90:
        badges.append("🔥 Top Performer")
    if row.get("improvement") and row["improvement"] > 10:
        badges.append("⬆️ Most Improved")
    if not badges:
        badges.append("–")
    return ", ".join(badges)


def main():
    st.title("EchoBoard Podcast Episode Leaderboard")

    rss_url = st.text_input("Enter podcast RSS feed URL")
    st.markdown(f"**Scores JSON path:** `{SCORES_JSON}`")

    if rss_url:
        episodes_df = parse_rss_feed(rss_url)
        scores_df = load_scores()
        df = merge_data(episodes_df, scores_df)
        df = normalize_scores(df)
        df["badges"] = df.apply(assign_badges, axis=1)
        df = df.sort_values(by="norm_score", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1

        st.dataframe(df[["rank", "title", "published", "norm_score", "badges"]])

        if st.button("Export leaderboard CSV"):
            df.to_csv(LEADERBOARD_CSV, index=False)
            st.success(f"Leaderboard exported to {LEADERBOARD_CSV.resolve()}")


if __name__ == "__main__":
    main()
