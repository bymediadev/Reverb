import os
import pandas as pd

DATA_PATH = "data/episodes.csv"
LEADERBOARD_PATH = "data/leaderboard.csv"


def recalculate_leaderboard():
    if not os.path.exists(DATA_PATH):
        print("No episode data found for leaderboard calculation.")
        return

    df = pd.read_csv(DATA_PATH)

    if df.empty:
        print("Episode data is empty.")
        return

    # Calculate an overall episode score (you can tweak the weights)
    # Example weighted average of ratings: audio 25%, flow 25%, guest energy 25%, structure 25%
    df["Score"] = (
        df["Audio Score"] * 0.25
        + df["Flow Score"] * 0.25
        + df["Guest Energy"] * 0.25
        + df["Structure Score"] * 0.25
    )

    # Group by episode (using 'Episode Title' & 'Release Date' for uniqueness)
    leaderboard = (
        df.groupby(["Episode Title", "Release Date"])
        .agg(
            {
                "Score": "mean",
                "Guest Name": "first",
                "Show": "first",
                "Audio Score": "mean",
                "Flow Score": "mean",
                "Guest Energy": "mean",
                "Structure Score": "mean",
            }
        )
        .reset_index()
    )

    # Sort by Score descending to rank best episodes at top
    leaderboard = leaderboard.sort_values(by="Score", ascending=False)

    # Add Rank column
    leaderboard["Rank"] = range(1, len(leaderboard) + 1)

    # Reorder columns
    leaderboard = leaderboard[
        [
            "Rank",
            "Episode Title",
            "Release Date",
            "Guest Name",
            "Show",
            "Score",
            "Audio Score",
            "Flow Score",
            "Guest Energy",
            "Structure Score",
        ]
    ]

    # Save leaderboard CSV
    os.makedirs(os.path.dirname(LEADERBOARD_PATH), exist_ok=True)
    leaderboard.to_csv(LEADERBOARD_PATH, index=False)
    print(f"Leaderboard recalculated and saved to {LEADERBOARD_PATH}")
