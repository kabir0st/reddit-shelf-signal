import os
import json
from datetime import datetime, timezone

import praw
from dotenv import load_dotenv

from libs.utils import (search_reddit_for_keyword_incremental,
                        send_discord_notification)


def load_existing_data(filename="reddit_search_results.json"):
    """Load existing data and return data with last timestamp."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Get last data pull timestamp
        metadata = data.get("metadata", {})
        last_timestamp = metadata.get("last_data_pull_timestamp_utc")
        if last_timestamp:
            last_timestamp = datetime.fromisoformat(last_timestamp).timestamp()
        else:
            # If no timestamp exists, use a very old timestamp to get all data
            last_timestamp = 0

        return data, last_timestamp
    except FileNotFoundError:
        print("No existing data file found. Starting fresh search.")
        return None, 0
    except Exception as e:
        print(f"Error loading existing data: {e}")
        return None, 0


def main():
    load_dotenv()
    reddit = praw.Reddit(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        password=os.getenv("USER_PASSWORD"),
        user_agent="Information Agent by Booksmandala",
        username=os.getenv("USER_NAME"),
    )
    print(f"Logged in as: {reddit.user.me()}")

    subs = [
        'technepal',
        'nepal',
        'nepalsocial',
    ]

    target_phrases = [
        'where to buy books', "bookstores", 'online book', 'pdf book',
        'booksmandala', 'books mandala', 'book store in nepal', 'online books',
        'where can i get this book', 'buy books online', 'book delivery nepal',
        'nepali bookstore'
    ]

    # Load existing data and get last timestamp
    existing_data, last_timestamp = load_existing_data()

    if last_timestamp > 0:
        timestamp_str = datetime.fromtimestamp(last_timestamp,
                                               tz=timezone.utc).isoformat()
    else:
        timestamp_str = 'Never'
    print(f"Last data pull timestamp: {timestamp_str}")

    # Search for new data after the last timestamp
    new_results = search_reddit_for_keyword_incremental(
        reddit, subs, target_phrases, last_timestamp, existing_data)

    # Send Discord notifications for new results
    if new_results:
        print(f"\n🔔 Found {len(new_results)} new results. "
              "Sending Discord notifications...")
        discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if discord_webhook_url:
            send_discord_notification(new_results, discord_webhook_url)
        else:
            print("⚠️ DISCORD_WEBHOOK_URL not found in environment "
                  "variables. Skipping notifications.")
    else:
        print("\n✅ No new results found since last check.")


if __name__ == "__main__":
    main()
