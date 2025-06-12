import time
from datetime import datetime, timedelta

from praw.models import MoreComments
from prawcore.exceptions import Forbidden, RequestException, ResponseException


def get_time_filter(days_back):
    """Map the number of days to a PRAW-compatible time_filter."""
    if days_back <= 1:
        return "day"
    if days_back <= 7:
        return "week"
    if days_back <= 31:  # Use 31 to safely cover a month
        return "month"
    if days_back <= 365:
        return "year"
    return "all"


def search_reddit_for_keyword(reddit_instance,
                              subs,
                              target_phrases,
                              days_back=1000):
    """
    Search Reddit comprehensively for posts and comments with target phrases.

    Args:
        reddit_instance: Authenticated PRAW Reddit instance.
        subs: List of subreddits to search.
        target_phrases: List of phrases to search for.
        days_back: Number of days back to search (default: 30).

    Returns:
        A list of dictionaries containing search results.
    """
    date_threshold = datetime.now() - timedelta(days=days_back)
    date_threshold_timestamp = date_threshold.timestamp()
    time_filter = get_time_filter(days_back)
    search_query = " OR ".join(f'"{phrase}"' for phrase in target_phrases)

    print("Searching Reddit for posts and comments...")
    print(
        f"Date filter: Items from {date_threshold.strftime('%Y-%m-%d')} onwards"
    )
    print(f"Subreddits: {', '.join(subs)}")
    print(f"Target phrases: {', '.join(target_phrases)}")
    print("-" * 80)

    all_results = []
    seen_urls = set()  # Use a set for efficient de-duplication

    def add_result(result):
        """Add a result if it hasn't been seen before."""
        if result["url"] not in seen_urls:
            all_results.append(result)
            seen_urls.add(result["url"])
            return True
        return False

    # EXPANDED: Search using multiple sort methods to cast a wider net
    search_sorts = ["relevance", "new", "comments"]

    for subreddit_name in subs:
        print(f"\n🔍 Searching in r/{subreddit_name}...")
        found_in_sub_overall = False
        try:
            subreddit = reddit_instance.subreddit(subreddit_name)
            for sort_method in search_sorts:
                print(
                    f"  📋 Searching submissions (sort: {sort_method}, time: {time_filter})..."
                )
                submissions = subreddit.search(
                    query=search_query,
                    sort=sort_method,
                    time_filter=time_filter,
                    limit=150,  # Increased limit for a wider search
                )

                for submission in submissions:
                    if submission.created_utc < date_threshold_timestamp:
                        continue
                    found_in_sub_overall = True

                    # 1. Process the Submission itself
                    sub_match_data = check_text_for_phrases(
                        f"{submission.title} {submission.selftext or ''}",
                        target_phrases,
                    )
                    if sub_match_data["matches"]:
                        result = create_submission_result(
                            submission, sub_match_data)
                        if add_result(result):
                            print(
                                f"    ✅ Found in submission: {submission.title[:60]}..."
                            )

                    # 2. Process all comments within the submission
                    try:
                        submission.comments.replace_more(limit=None)
                        for comment in submission.comments.list():
                            if isinstance(comment, MoreComments):
                                continue
                            if comment.created_utc < date_threshold_timestamp:
                                continue
                            comment_match_data = check_text_for_phrases(
                                comment.body, target_phrases)
                            if comment_match_data["matches"]:
                                result = create_comment_result(
                                    comment, comment_match_data)
                                if add_result(result):
                                    print(
                                        f"      ✅ Found in comment by u/{result['author']}"
                                    )
                    except Exception as e:
                        print(
                            f"      ❌ Error processing comments for {submission.id}: {e}"
                        )
                time.sleep(2)  # Rate limiting between different sort API calls

            if not found_in_sub_overall:
                print(
                    "  -> No submissions found matching criteria in this subreddit."
                )

        except (RequestException, ResponseException, Forbidden) as e:
            print(f"❌ API error searching r/{subreddit_name}: {e}")
            time.sleep(10)
        except Exception as e:
            print(f"❌ Unexpected error in r/{subreddit_name}: {e}")
            time.sleep(5)

    display_results(all_results)
    return all_results


def check_text_for_phrases(text, target_phrases):
    """
    Check text for any target phrases (case-insensitive).

    Returns:
        A dictionary with 'matches' (list) and 'context' (text preview).
    """
    if not text or text in ["[deleted]", "[removed]"]:
        return {"matches": [], "context": ""}

    text_lower = text.lower()
    matches = [
        phrase for phrase in target_phrases if phrase.lower() in text_lower
    ]

    preview = text[:200] + "..." if len(text) > 200 else text
    if matches:
        first_match_lower = matches[0].lower()
        match_pos = text_lower.find(first_match_lower)
        if match_pos != -1:
            start = max(0, match_pos - 70)
            end = min(len(text), match_pos + len(first_match_lower) + 70)
            preview = f"...{text[start:end]}..."
    return {"matches": matches, "context": preview.replace("\n", " ")}


def create_submission_result(submission, match_data):
    """Create a result dictionary for a submission."""
    return {
        "type":
        "submission",
        "subreddit":
        submission.subreddit.display_name,
        "title":
        submission.title,
        "author":
        str(submission.author) if submission.author else "[deleted]",
        "created":
        datetime.fromtimestamp(submission.created_utc),
        "url":
        f"https://reddit.com{submission.permalink}",
        "score":
        submission.score,
        "num_comments":
        submission.num_comments,
        "matching_phrases":
        match_data["matches"],
        "text_preview":
        match_data["context"],
        "full_text": (f"{submission.title}\n\n{submission.selftext}"
                      if submission.selftext else submission.title),
    }


def create_comment_result(comment, match_data):
    """Create a result dictionary for a comment."""
    return {
        "type": "comment",
        "subreddit": comment.subreddit.display_name,
        "title": f"Comment on: {comment.submission.title[:60]}...",
        "author": str(comment.author) if comment.author else "[deleted]",
        "created": datetime.fromtimestamp(comment.created_utc),
        "url": f"https://reddit.com{comment.permalink}",
        "score": comment.score,
        "matching_phrases": match_data["matches"],
        "text_preview": match_data["context"],
        "parent_submission": comment.submission.title,
        "full_text": comment.body,
    }


def display_results(results):
    """Display the search results in a formatted way."""
    if not results:
        print("\n❌ No results found matching the criteria.")
        return

    print(f"\n🎉 Found {len(results)} total unique results:")
    print("=" * 80)
    results.sort(key=lambda x: (-x["score"], x["created"]), reverse=True)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result['type'].upper()}] r/{result['subreddit']}")
        print(f"   📝 {result['title']}")
        print(f"   👤 u/{result['author']}"
              f" | 📅 {result['created'].strftime('%Y-%m-%d %H:%M')}"
              f" | ⬆️ {result['score']}")
        print(
            f"   🎯 Matched Keyword(s): {', '.join(result['matching_phrases'])}"
        )
        print(f"   📄 Preview: {result['text_preview']}")
        print(f"   🔗 {result['url']}")
        if result["type"] == "comment":
            print(f"   📋 Parent post: {result['parent_submission']}")


def save_results_to_file(results, filename="reddit_search_results.txt"):
    """Save search results to a text file with improved formatting."""
    if not results:
        print("\n💾 No results to save.")
        return

    all_phrases = set(p for r in results for p in r["matching_phrases"])

    with open(filename, "w", encoding="utf-8") as f:
        f.write("Reddit Search Results - "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Found {len(results)} results for phrases: "
                f"{', '.join(sorted(list(all_phrases)))}\n")
        f.write("=" * 80 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(
                f"{i}. [{result['type'].upper()}] r/{result['subreddit']}\n")
            f.write(f"   Title: {result['title']}\n")
            f.write(f"   Author: u/{result['author']}\n")
            f.write(
                f"   Date: {result['created'].strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"   Score: {result['score']}\n")
            if result.get("num_comments") is not None:
                f.write(f"   Comments: {result['num_comments']}\n")
            f.write(
                f"   Matched Keyword(s): {', '.join(result['matching_phrases'])}\n"
            )
            f.write(f"   URL: {result['url']}\n")
            f.write(f"   Preview:\n{result['text_preview']}\n")
            if result["type"] == "comment":
                f.write(f"   Parent post: {result['parent_submission']}\n")
            f.write("\n" + "-" * 80 + "\n\n")

    print(f"\n💾 Results saved to {filename}")
