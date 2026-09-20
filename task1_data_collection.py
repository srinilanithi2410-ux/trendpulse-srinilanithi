import requests
import json
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


# Hacker News API links
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Required header
headers = {
    "User-Agent": "TrendPulse/1.0"
}


# Categories and keywords
categories = {
    "technology": [
        "AI", "software", "tech", "code", "computer",
        "data", "cloud", "API", "GPU", "LLM"
    ],

    "worldnews": [
        "war", "government", "country", "president",
        "election", "climate", "attack", "global"
    ],

    "sports": [
        "NFL", "NBA", "FIFA", "sport", "game",
        "team", "player", "league", "championship"
    ],

    "science": [
        "research", "study", "space", "physics",
        "biology", "discovery", "NASA", "genome"
    ],

    "entertainment": [
        "movie", "film", "music", "Netflix",
        "game", "book", "show", "award", "streaming"
    ]
}


# Get first 500 top story IDs
def get_top_stories():

    try:
        response = requests.get(
            TOP_STORIES_URL,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        return response.json()[:500]

    except requests.RequestException as error:
        print("Error getting top stories:", error)
        return []


# Download one story
def get_story(story_id):

    try:
        url = ITEM_URL.format(story_id)

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        print("Error getting story", story_id, ":", error)
        return None


# Download stories faster using multiple workers
def download_stories(story_ids):

    stories = []

    print("Downloading 500 stories...")

    # Download 10 stories at the same time
    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [
            executor.submit(get_story, story_id)
            for story_id in story_ids
        ]

        completed = 0

        for future in as_completed(futures):

            story = future.result()

            if story is not None:
                stories.append(story)

            completed += 1

            # Show progress every 50 stories
            if completed % 50 == 0:
                print(f"Downloaded {completed}/500 stories")

    return stories


# Check title for keywords
def title_matches(title, keywords):

    title = title.lower()

    for keyword in keywords:

        if keyword.lower() in title:
            return True

    return False


# Categorise stories
def collect_stories(downloaded_stories):

    all_stories = []

    for category, keywords in categories.items():

        count = 0

        print(f"Checking category: {category}")

        for story in downloaded_stories:

            # Maximum 25 per category
            if count >= 25:
                break

            title = story.get("title")

            if not title:
                continue

            if title_matches(title, keywords):

                story_data = {
                    "post_id": story.get("id"),
                    "title": title,
                    "category": category,
                    "score": story.get("score", 0),
                    "num_comments": story.get("descendants", 0),
                    "author": story.get("by", "unknown"),
                    "collected_at": datetime.now().isoformat()
                }

                all_stories.append(story_data)

                count += 1

        print(f"Found {count} stories for {category}")

        # Required by assignment
        time.sleep(2)

    return all_stories


# Save JSON file
def save_json(stories):

    os.makedirs("data", exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")

    filename = f"data/trends_{today}.json"

    with open(filename, "w", encoding="utf-8") as file:

        json.dump(
            stories,
            file,
            indent=4,
            ensure_ascii=False
        )

    return filename


# Main program
def main():

    print("Starting TrendPulse...")

    # Get IDs
    story_ids = get_top_stories()

    if not story_ids:
        print("No stories found.")
        return

    print(f"Found {len(story_ids)} story IDs")

    # Download stories
    downloaded_stories = download_stories(story_ids)

    print(f"Successfully downloaded {len(downloaded_stories)} stories")

    # Categorise
    stories = collect_stories(downloaded_stories)

    # Save JSON
    filename = save_json(stories)

    # Required final output
    print()
    print(f"Collected {len(stories)} stories. Saved to {filename}")


if __name__ == "__main__":
    main()