#!/usr/bin/env python3
# fetch_chapter.py
# Usage: python fetch_chapter.py
# Requires: requests

import os, json, requests, sys
from datetime import datetime

BOOKS_FILE = "books.json"
PROGRESS_FILE = "progress.json"
OUT_DIR = "chapters"
MIN_LENGTH = 30  # fetched text must be longer than this to be considered valid

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def make_filename(prefix, chapter):
    return f"{prefix}_ch{chapter}.txt"

def fetch_url(url, timeout=20):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DailyBookBot/1.0)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        return r.status_code, r.text
    except Exception as e:
        print("Fetch error:", e)
        return None, None

def main():
    books = load_json(BOOKS_FILE)
    progress = load_json(PROGRESS_FILE)
    if not progress:
        print("No progress.json found. Please create one.")
        sys.exit(1)

    book = progress.get("book")
    chapter = progress.get("chapter", 1)

    if book not in books:
        print(f"Book '{book}' not found in {BOOKS_FILE}.")
        sys.exit(1)

    source = books[book]
    # build URL
    url = "https://github.com/minntant-art/daily-book-bot/blob/main/book/chapters.txt"
    if source.get("type") == "pattern":
        url = source["pattern"].format(chapter=chapter)
    elif source.get("type") == "list":
        lst = source.get("list", [])
        idx = chapter - 1
        if idx < 0 or idx >= len(lst):
            print("Chapter index out of range for list source.")
            sys.exit(0)  # no error, just nothing to fetch
        url = lst[idx]
    else:
        print("Unknown source type:", source.get("type"))
        sys.exit(1)

    print("Fetching:", url)
    status, content = fetch_url(url)
    if status != 200 or not content or len(content.strip()) < MIN_LENGTH:
        print(f"Failed to fetch valid content (status={status}, len={0 if not content else len(content)}).")
        # exit 0 so Actions doesn't mark as failed if nothing new
        sys.exit(0)

    # write file
    os.makedirs(OUT_DIR, exist_ok=True)
    prefix = source.get("file_prefix", book.replace(" ", "-").lower())
    filename = make_filename(prefix, chapter)
    filepath = os.path.join(OUT_DIR, filename)

    # avoid overwriting existing file
    if os.path.exists(filepath):
        print("Already have file:", filepath)
        sys.exit(0)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("Saved:", filepath)

    # update progress (next chapter)
    progress["chapter"] = chapter + 1
    save_json(PROGRESS_FILE, progress)
    print("Progress updated:", progress)

if __name__ == "__main__":
    main()
