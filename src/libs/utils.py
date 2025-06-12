import json
import time
from datetime import datetime, timedelta, timezone

from praw.models import MoreComments
from prawcore.exceptions import Forbidden, RequestException, ResponseException


def get_time_filter(days_back):
    """Map the number of days to a PRAW-compatible time_filter."""
    if days_back <= 1:
        return "day"
    if days_back <= 7:
        return "week"
    if days_back <= 31:
        return "month"
    if days_back <= 365:
        return "year"
    return "all"


def search_reddit_for_keyword(reddit_instance,
                              subs,
                              target_phrases,
                              days_back=30):
    """
    Search Reddit comprehensively and save detailed results to a JSON file.

    Args:
        reddit_instance: Authenticated PRAW Reddit instance.
        subs: List of subreddits to search.
        target_phrases: List of phrases to search for.
        days_back: Number of days back to search (default: 30).

    Returns:
        A list of dictionaries containing detailed search results.
    """
    date_threshold = datetime.now(timezone.utc) - timedelta(days=days_back)
    date_threshold_timestamp = date_threshold.timestamp()
    search_query = " OR ".join(f'"{phrase}"' for phrase in target_phrases)

    print("Searching Reddit for posts and comments...")
    print(f"Date filter: Items from {date_threshold.strftime('%Y-%m-%d')}"
          " onwards")
    print(f"Subreddits: {', '.join(subs)}")
    print(f"Target phrases: {', '.join(target_phrases)}")
    print("-" * 80)

    all_results = []
    seen_ids = set()  # Use ID for de-duplication (more robust than URL)

    def add_result(result):
        """Add a result if it hasn't been seen before."""
        if result["id"] not in seen_ids:
            all_results.append(result)
            seen_ids.add(result["id"])
            return True
        return False

    search_sorts = ["relevance", "new", "comments"]

    for subreddit_name in subs:
        print(f"\n🔍 Searching in r/{subreddit_name}...")
        try:
            subreddit = reddit_instance.subreddit(subreddit_name)
            for sort_method in search_sorts:
                time_filter = get_time_filter(days_back)
                print(f"  📋 Searching submissions (sort: {sort_method}, "
                      f"time: {time_filter})...")
                submissions = subreddit.search(
                    query=search_query,
                    sort=sort_method,
                    time_filter=time_filter,
                    limit=150,
                )

                for submission in submissions:
                    if submission.created_utc < date_threshold_timestamp:
                        continue

                    # 1. Process the Submission itself
                    sub_match_data = check_text_for_phrases(
                        f"{submission.title} {submission.selftext or ''}",
                        target_phrases,
                    )
                    if sub_match_data["matches"]:
                        result = create_submission_json_result(
                            submission, sub_match_data)
                        if add_result(result):
                            print(
                                f"    ✅ Found in submission: {submission.id}")

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
                                result = create_comment_json_result(
                                    comment, comment_match_data)
                                if add_result(result):
                                    print("      ✅ Found in comment: "
                                          f"{comment.id}")
                    except Exception as e:
                        print(f"      ❌ Error processing comments"
                              f" for {submission.id}: {e}")
                time.sleep(2)
        except (RequestException, ResponseException, Forbidden) as e:
            print(f"❌ API error searching r/{subreddit_name}: {e}")
            time.sleep(10)
        except Exception as e:
            print(f"❌ Unexpected error in r/{subreddit_name}: {e}")
            time.sleep(5)

    display_results(all_results)
    save_results_to_json(all_results, target_phrases)
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

    preview = ""
    if matches:
        first_match_lower = matches[0].lower()
        match_pos = text_lower.find(first_match_lower)
        if match_pos != -1:
            start = max(0, match_pos - 70)
            end = min(len(text), match_pos + len(first_match_lower) + 70)
            preview = f"...{text[start:end]}..."
    return {"matches": matches, "context_preview": preview.replace("\n", " ")}


def create_submission_json_result(submission, match_data):
    """Create a detailed result dictionary for a submission."""
    author_name = str(submission.author) if submission.author else "[deleted]"
    return {
        "type":
        "submission",
        "id":
        submission.id,
        "matching_phrases":
        match_data["matches"],
        "context_preview":
        match_data["context_preview"],
        "subreddit":
        submission.subreddit.display_name,
        "title":
        submission.title,
        "author_name":
        author_name,
        "created_utc":
        submission.created_utc,
        "created_iso":
        datetime.fromtimestamp(submission.created_utc,
                               tz=timezone.utc).isoformat(),
        "url":
        f"https://reddit.com{submission.permalink}",
        "score":
        submission.score,
        "upvote_ratio":
        submission.upvote_ratio,
        "num_comments":
        submission.num_comments,
        "is_self":
        submission.is_self,
        "stickied":
        submission.stickied,
        "locked":
        submission.locked,
        "full_text": (f"{submission.title}\n\n{submission.selftext}"
                      if submission.is_self else submission.url),
    }


def create_comment_json_result(comment, match_data):
    """Create a detailed result dictionary for a comment."""
    author_name = str(comment.author) if comment.author else "[deleted]"
    return {
        "type":
        "comment",
        "id":
        comment.id,
        "matching_phrases":
        match_data["matches"],
        "context_preview":
        match_data["context_preview"],
        "subreddit":
        comment.subreddit.display_name,
        "parent_submission_id":
        comment.submission.id,
        "parent_submission_title":
        comment.submission.title,
        "author_name":
        author_name,
        "created_utc":
        comment.created_utc,
        "created_iso":
        datetime.fromtimestamp(comment.created_utc,
                               tz=timezone.utc).isoformat(),
        "url":
        f"https://reddit.com{comment.permalink}",
        "score":
        comment.score,
        "depth":
        comment.depth,
        "is_submitter":
        comment.is_submitter,
        "stickied":
        comment.stickied,
        "locked":
        comment.locked,
        "full_text":
        comment.body,
    }


def display_results(results):
    """Display a summary of the search results in the console."""
    if not results:
        print("\n❌ No results found matching the criteria.")
        return

    print(f"\n🎉 Found {len(results)} total unique results:")
    print("=" * 80)
    results.sort(key=lambda x: (-x["score"], x["created_utc"]), reverse=True)
    for i, result in enumerate(results, 1):
        created_dt = datetime.fromisoformat(result['created_iso'])
        title = result.get(
            'title', f"Comment on: "
            f"{result.get('parent_submission_title', 'N/A')[:60]}...")
        print(f"\n{i}. [{result['type'].upper()}] r/{result['subreddit']}")
        print(f"   📝 {title}")
        print(f"   👤 u/{result['author_name']}"
              f" | 📅 {created_dt.strftime('%Y-%m-%d %H:%M')}"
              f" | ⬆️ {result['score']}")
        print(
            f"   🎯 Matched Keyword(s): {', '.join(result['matching_phrases'])}"
        )
        print(f"   📄 Preview: {result['context_preview']}")
        print(f"   🔗 {result['url']}")


def save_results_to_json(results,
                         target_phrases,
                         filename="reddit_search_results.json"):
    """Save detailed search results to a structured JSON file."""
    if not results:
        print("\n💾 No results to save.")
        return

    # Sort results by score for the final file
    results.sort(key=lambda x: (-x["score"], x["created_utc"]), reverse=True)

    output_data = {
        "metadata": {
            "search_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "target_phrases": target_phrases,
            "total_results": len(results),
        },
        "results": results,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    print(f"\n💾 Results saved to {filename}")
