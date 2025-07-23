import os
import json
import pandas as pd
import datetime
import streamlit as st
import re

from utils.feedback_utils import (
    save_feedback,
    generate_weekly_summary,
    send_summary_email,
    load_feedback,
    generate_sentiment_scores,
    get_comment_wordcloud,
    generate_ai_insights,
    export_pdf_summary,
)
from utils.rss_utils import fetch_latest_episodes
import utils.leaderboard_utils as leaderboard_utils

# ---- Add your new imports for Spotify/YouTube fetch + AI feedback ----
from utils.spotify_utils import fetch_spotify_podcasts
from utils.youtube_utils import fetch_podcast_context
from utils.ai_feedback import generate_ai_feedback

# --- Constants ---
FEEDBACK_CACHE_FILE = "feedback_cache.json"

# --- Helper Functions for AI Feedback caching ---
def load_feedback_cache():
    if os.path.exists(FEEDBACK_CACHE_FILE):
        with open(FEEDBACK_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_feedback_cache(cache):
    with open(FEEDBACK_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def get_feedback_for_podcast(podcast, cache):
    # Spotify podcasts have 'id', YouTube podcasts have 'video_id'
    podcast_id = podcast.get("id") or podcast.get("video_id")
    if not podcast_id:
        return "(Missing podcast ID)"

    if podcast_id in cache:
        return cache[podcast_id]

    feedback = generate_ai_feedback(podcast)
    cache[podcast_id] = feedback
    save_feedback_cache(cache)
    return feedback

# --- Utility ---
def strip_html_tags(text):
    if not text:
        return ""
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="EchoBoard: Episode Feedback", layout="wide")
st.title("Reverb - Episode Feedback Tracker")

# --- Tabs for UI Separation ---
tab1, tab2 = st.tabs(["Manual Episode Feedback", "Podcast AI Feedback"])

# -------------------------
# Tab 1: Manual Episode Feedback (your existing UI)
# -------------------------
with tab1:
    st.subheader("🔄 Auto-Fetch From RSS")
    rss_url = "https://anchor.fm/s/7ae43ac/podcast/rss"
    episodes = fetch_latest_episodes(rss_url)

    if episodes:
        selected = st.selectbox("Select an Episode", [e["title"] for e in episodes])
        chosen = next((e for e in episodes if e["title"] == selected), None)
        if chosen:
            episode_title = st.text_input("Episode Title", value=chosen["title"])
            release_date = st.date_input(
                "Planned Release Date", value=pd.to_datetime(chosen["published"]).date()
            )
            clean_summary = strip_html_tags(chosen.get("summary", ""))
            st.markdown(f"**Summary:** {clean_summary}")
    else:
        episode_title = st.text_input("Episode Title")
        release_date = st.date_input("Planned Release Date", value=datetime.date.today())

    st.header("🎧 Episode Metadata")
    guest_name = st.text_input("Guest Name")
    show_name = st.selectbox("Show", ["Case and Fire", "Why Mastermind", "Other"])
    date_recorded = st.date_input("Date Recorded", value=datetime.date.today())

    st.header("📊 Internal Ratings")
    audio_score = st.slider("Audio Quality", 1, 5, 3)
    flow_score = st.slider("Episode Flow", 1, 5, 3)
    guest_energy = st.slider("Guest Energy", 1, 5, 3)
    structure_score = st.slider("Segment Structure", 1, 5, 3)

    st.header("📝 Feedback Notes (Tag & Timestamp)")
    comment = st.text_area(
        "Write your note with timestamp and tags (e.g. 15:32 - Tech Glitch in Guest Audio)"
    )
    comment_category = st.multiselect(
        "Category Tags",
        ["Audio", "Content", "Guest", "Tech", "Layout", "Audience", "Other"],
    )

    st.header("👥 Community Feedback")
    community_sentiment = st.text_area(
        "Audience Reactions / DM / Discord / Social Media Feedback"
    )
    clip_notes = st.text_area("Clip Performance Notes")

    if st.button("✅ Submit Episode Feedback"):
        save_feedback(
            episode_title,
            guest_name,
            show_name,
            date_recorded,
            release_date,
            audio_score,
            flow_score,
            guest_energy,
            structure_score,
            comment,
            comment_category,
            community_sentiment,
            clip_notes,
        )
        st.success("Feedback logged for this episode.")

    st.markdown("---")

    st.header("📤 Generate Weekly Summary")
    if st.button("🗃️ Export Last Week's Summary"):
        generate_weekly_summary()
        st.success("Summary saved to /exports/weekly_summary.csv")

    st.header("📄 Export PDF Report")
    if st.button("💾 Save Weekly Summary as PDF"):
        export_pdf_summary()
        st.success("PDF summary saved to /exports/")

    st.header("📧 Email Summary Report")
    if st.button("📬 Email Weekly Summary to Team"):
        send_summary_email()
        st.success("Summary emailed successfully.")

    st.markdown("---")

    st.header("📈 Dashboard & AI Insights")
    feedback_df = load_feedback()

    if feedback_df.empty:
        st.warning("No feedback data yet. Submit feedback above to begin tracking.")
    else:
        st.subheader("🔢 Average Ratings")
        st.bar_chart(
            feedback_df[
                ["Audio Score", "Flow Score", "Guest Energy", "Structure Score"]
            ].mean()
        )

        st.subheader("☁️ Word Cloud of Comments")
        wc_fig = get_comment_wordcloud(feedback_df)
        if wc_fig:
            st.pyplot(wc_fig)
        else:
            st.info("No comment data available to generate word cloud.")

        st.subheader("📉 Sentiment Over Time")
        sentiment_df = generate_sentiment_scores(feedback_df)
        if not sentiment_df.empty and "Sentiment" in sentiment_df.columns:
            st.line_chart(sentiment_df.set_index("Timestamp")["Sentiment"])
        else:
            st.info("No sentiment data available.")

        st.subheader("🏆 Leaderboard")
        leaderboard_file = "data/leaderboard.csv"
        if os.path.exists(leaderboard_file):
            leaderboard_df = pd.read_csv(leaderboard_file)
            st.dataframe(leaderboard_df.style.format({"Score": "{:.2f}"}))
        else:
            st.info("No leaderboard data available yet.")

        if st.button("🔄 Recalculate Rankings"):
            leaderboard_utils.recalculate_leaderboard()
            st.success("Leaderboard recalculated!")

        st.subheader("🤖 AI-Generated Weekly Summary Insights")
        insights = generate_ai_insights(feedback_df)
        st.write(insights)

# -------------------------
# Tab 2: Podcast AI Feedback
# -------------------------
with tab2:
    st.header("🎙️ Podcast AI Feedback (Spotify / YouTube)")
    platform = st.selectbox("Select Platform", ["Spotify", "YouTube"])
    query = st.text_input("Search Podcasts by Keyword", key="podcast_ai_query")

    if st.button("Fetch Podcasts and Generate AI Feedback", key="fetch_podcast_ai"):
        if not query.strip():
            st.warning("Please enter a search keyword.")
        else:
            feedback_cache = load_feedback_cache()
            with st.spinner(f"Fetching podcasts from {platform}..."):
                if platform == "Spotify":
                    podcasts = fetch_spotify_podcasts(query)
                else:
                    podcasts = fetch_podcast_context(query)

            if not podcasts:
                st.info("No podcasts found for your query.")
            else:
                for p in podcasts:
                    title = p.get("name") or p.get("title") or "Untitled Podcast"
                    st.subheader(title)
                    st.markdown(f"**Description:** {p.get('description', 'N/A')[:300]}...")
                    transcript = p.get("transcript")
                    if transcript:
                        st.markdown(f"**Transcript snippet:** {transcript[:500]}...")
                    comments = p.get("comments", [])
                    if comments:
                        st.markdown("**Comments:**")
                        for c in comments[:3]:
                            st.write(f"- {c}")

                    feedback = get_feedback_for_podcast(p, feedback_cache)
                    st.markdown(f"### 🤖 AI Feedback:\n{feedback}")
                    st.markdown("---")
