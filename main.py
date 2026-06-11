# ============================================================
#  Finance News Summarizer Bot  —  main.py  (Prototype v1)
# ============================================================
#
#  BEFORE RUNNING — install dependencies:
#  pip3 install requests openai python-telegram-bot schedule
#
# ============================================================

import os
from dotenv import load_dotenv
import requests
import openai
import schedule
import time
import asyncio
from telegram import Bot

load_dotenv()

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
NEWS_API_KEY      = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")


# ─────────────────────────────────────────
#  STEP 1 — Fetch top finance headlines
# ─────────────────────────────────────────
def fetch_news(num_articles=8):
    """
    Calls NewsAPI and returns a plain-text list of headlines + descriptions.
    """
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "category": "business",
        "language": "en",
        "pageSize": num_articles,
        "apiKey": NEWS_API_KEY,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    articles = response.json().get("articles", [])

    if not articles:
        return "No articles found."

    # Build a simple numbered text block to send to the LLM
    news_text = ""
    for i, article in enumerate(articles, start=1):
        title       = article.get("title", "No title")
        description = article.get("description", "")
        news_text  += f"{i}. {title}\n   {description}\n\n"

    return news_text


# ─────────────────────────────────────────
#  STEP 2 — Summarize with OpenAI
# ─────────────────────────────────────────
def summarize(news_text):
    """
    Sends the headlines to GPT and returns a short bullet-point summary.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
You are a concise financial analyst assistant.
Below are today's top business/finance headlines.
Summarize them into 5 clear bullet points.
Focus on the most important market-moving information.
Keep each bullet under 2 sentences.

Headlines:
{news_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
    )

    summary = response.choices[0].message.content.strip()
    return summary


# ─────────────────────────────────────────
#  STEP 3 — Send via Telegram
# ─────────────────────────────────────────
async def send_telegram(text):
    """
    Sends the summary to your Telegram chat.
    """
    bot     = Bot(token=TELEGRAM_TOKEN)
    message = f"📊 *Finance News Summary by PTM*\n\n{text}"

    await bot.send_message(
        chat_id    = TELEGRAM_CHAT_ID,
        text       = message,
        parse_mode = "Markdown",
    )
    print(" Message sent to Telegram.")


# ─────────────────────────────────────────
#  STEP 4 — Main job (chains all 3 steps)
# ─────────────────────────────────────────
def job():
    print(" Fetching news...")
    try:
        news    = fetch_news()
        print(" Summarizing...")
        summary = summarize(news)
        print(" Sending to Telegram...")
        asyncio.run(send_telegram(summary))
    except Exception as e:
        print(f" Error: {e}")


# ─────────────────────────────────────────
#  STEP 5 — Schedule (runs while script is open)
# ─────────────────────────────────────────
if __name__ == "__main__":

    # --- Run once immediately so can test right away ---
    print(" Running immediately for first test...")
    job()

    # --- Schedule for every day at these times ---
    schedule.every().day.at("08:00").do(job)   # morning briefing
    schedule.every().day.at("18:00").do(job)   # evening briefing

    print(" Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(59)    # checks every 30 seconds