import os
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from textblob import TextBlob
import openai
from fpdf import FPDF

# --- Paths ---
DATA_PATH = "data/episodes.csv"
EXPORT_PATH = "exports/weekly_summary.csv"

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


# === Feedback Storage ===
def save_feedback(
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
):

    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    new_entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Episode Title": episode_title,
        "Guest Name": guest_name,
        "Show": show_name,
        "Date Recorded": date_recorded.strftime("%Y-%m-%d"),
        "Release Date": release_date.strftime("%Y-%m-%d"),
        "Audio Score": audio_score,
        "Flow Score": flow_score,
        "Guest Energy": guest_energy,
        "Structure Score": structure_score,
        "Comment": comment,
        "Comment Category": ", ".join(comment_category),
        "Community Sentiment": community_sentiment,
        "Clip Notes": clip_notes,
    }

    df_new = pd.DataFrame([new_entry])
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(DATA_PATH, index=False)


# === Weekly Summary CSV ===
def generate_weekly_summary():
    if not os.path.exists(DATA_PATH):
        return

    df = pd.read_csv(DATA_PATH, parse_dates=["Timestamp"])
    one_week_ago = datetime.now() - timedelta(days=7)
    df_recent = df[df["Timestamp"] >= one_week_ago]

    if df_recent.empty:
        pd.DataFrame([{"Message": "No data in past 7 days."}]).to_csv(
            EXPORT_PATH, index=False
        )
        return

    summary = {
        "Episodes Reviewed": df_recent.shape[0],
        "Avg Audio Score": round(df_recent["Audio Score"].mean(), 2),
        "Avg Flow Score": round(df_recent["Flow Score"].mean(), 2),
        "Avg Guest Energy": round(df_recent["Guest Energy"].mean(), 2),
        "Avg Structure Score": round(df_recent["Structure Score"].mean(), 2),
    }

    os.makedirs("exports", exist_ok=True)
    df_recent.to_csv(EXPORT_PATH, index=False)
    pd.DataFrame([summary]).to_csv(
        EXPORT_PATH.replace(".csv", "_summary.csv"), index=False
    )


# === Email Summary ===
def send_summary_email():
    sender = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")
    recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")

    summary_file = EXPORT_PATH.replace(".csv", "_summary.csv")
    if not os.path.exists(summary_file):
        return

    subject = "📊 EchoBoard Weekly Summary"
    body = "Attached is the latest weekly performance and feedback summary for BY Media podcast episodes."

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    with open(summary_file, "rb") as f:
        file_data = f.read()
        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="csv",
            filename="weekly_summary.csv",
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)


# === Load & Process Feedback ===
def load_feedback():
    return pd.read_csv(DATA_PATH) if os.path.exists(DATA_PATH) else pd.DataFrame()


def generate_sentiment_scores(df):
    if df.empty or "Comment" not in df.columns:
        return df
    df = df.copy()
    df["Sentiment"] = (
        df["Comment"].fillna("").apply(lambda text: TextBlob(text).sentiment.polarity)
    )
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    return df


def get_comment_wordcloud(df):
    if df.empty or "Comment" not in df.columns:
        return None

    text = " ".join(df["Comment"].dropna().tolist()).strip()
    if not text:
        return None

    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(
        text
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    return fig


# === AI Insights ===
def generate_ai_insights(df):
    if OPENAI_API_KEY is None or df.empty:
        return "OpenAI API key not set or no feedback data."

    comments = df["Comment"].dropna().tolist()
    if not comments:
        return "No comment data available."

    combined_text = "\n\n".join(comments[:10])  # Max 10 to stay within token limits

    prompt = (
        "You are an AI assistant analyzing podcast episode feedback.\n"
        "Summarize key insights, trends, and improvement areas based on this feedback:\n\n"
        f"{combined_text}\n\n"
        "Provide a concise summary."
    )

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=250,
            temperature=0.7,
            n=1,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error generating AI insights: {e}"


# === PDF Export ===
def export_pdf_summary():
    summary_file = EXPORT_PATH.replace(".csv", "_summary.csv")
    if not os.path.exists(summary_file):
        return

    df = pd.read_csv(summary_file)
    filename = f"exports/weekly_summary_{datetime.now().strftime('%Y-%m-%d')}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="EchoBoard Weekly Summary", ln=True, align="C")
    pdf.ln(10)

    for col in df.columns:
        value = df[col].iloc[0]
        pdf.cell(200, 10, txt=f"{col}: {value}", ln=True)

    os.makedirs("exports", exist_ok=True)
    pdf.output(filename)
