import os

import praw
from dotenv import load_dotenv

from libs.utils import save_results_to_file, search_reddit_for_keyword


def main():
    load_dotenv()  # take environment variables from .env.
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
        'where to buy books', 'booksmandala', 'books mandala',
        'book store in nepal', 'online books', 'where can i get this book',
        'buy books online', 'book delivery nepal', 'nepali bookstore'
    ]
    results = search_reddit_for_keyword(reddit, subs, target_phrases)
    save_results_to_file(results, "book_mentions.txt")


if __name__ == "__main__":
    main()
