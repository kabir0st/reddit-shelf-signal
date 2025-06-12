# 📚 Reddit Book Mention Bot 🤖

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Overview

This project is a Python-based Reddit bot designed to scan specified subreddits for mentions related to buying books, particularly in the context of Nepal. When it finds relevant posts or comments, it logs these mentions into a file. This is useful for businesses like **Booksmandala** to track potential customer inquiries or discussions about book purchasing.

## ✨ Features

-   Searches multiple subreddits.
-   Looks for a configurable list of keywords and phrases.
-   Authenticates with Reddit using API credentials.
-   Saves found mentions to a local file (`book_mentions.txt`).
-   Easy to configure and run.

## 🛠️ Getting Started

Follow these steps to get the bot up and running on your local machine.

### Prerequisites

-   Python 3.12+
-   `uv` (or `pip`) for package management
-   A Reddit account and API credentials

### ⚙️ Installation & Setup

1.  **Clone the repository:**
    

2.  **Install dependencies:**
    This project uses `uv` for package management. If you have `uv` installed, you can create a virtual environment and install dependencies from [`pyproject.toml`](pyproject.toml:0):
    ```bash
    uv venv
    uv pip install -r requirements.txt 
    # or if pyproject.toml is configured for it:
    # uv pip install . 
    ```
    Alternatively, if you prefer using `pip`:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    pip install praw python-dotenv
    ```

3.  **Set up Environment Variables:**
    Create a file named `.env` in the root directory of the project. Add your Reddit API credentials to this file:
    ```env
    CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
    CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET"
    USER_PASSWORD="YOUR_REDDIT_USER_PASSWORD"
    USER_NAME="YOUR_REDDIT_USERNAME"
    ```
    Replace the placeholder values with your actual Reddit API details. You can obtain these by creating a new "script" app on Reddit's [app preferences page](https://www.reddit.com/prefs/apps).

### ▶️ Running the Bot

Once the setup is complete, you can run the bot using the following command:

```bash
python main.py
```

The bot will log in to Reddit and start searching the configured subreddits for the target phrases. Any matches found will be saved in the [`book_mentions.txt`](book_mentions.txt:0) file in the project's root directory.

## 📋 Configuration

You can customize the bot's behavior by modifying the following in [`main.py`](main.py:9):

-   **Subreddits to search (`subs` list):**
    ```python
    subs = [
        'technepal',
        'nepal',
        'nepalsocial',
        # Add more subreddits here
    ]
    ```

-   **Target phrases to look for (`target_phrases` list):**
    ```python
    target_phrases = [
        'where to buy books', 'booksmandala', 'books mandala',
        'book store in nepal', 'online books', 'where can i get this book',
        'buy books online', 'book delivery nepal', 'nepali bookstore'
        # Add more phrases here
    ]
    ```

## 📁 Project Structure

```
.
├── .gitignore
├── .python-version
├── book_mentions.txt   # Output file for mentions
├── main.py             # Main script to run the bot
├── pyproject.toml      # Project metadata and dependencies
├── README.md           # This file
├── uv.lock             # uv lock file
└── libs/
    └── utils.py        # Utility functions for Reddit search and saving results
```

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or find any issues, please feel free to:

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (if one exists, or specify directly).

---

Happy Searching! 🕵️‍♂️📖