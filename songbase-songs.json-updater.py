#!/usr/bin/env python3
"""
Songbase dump utility — fetch songs from songbase.life and write to a JSON file.
This is a lightweight replacement that removes the PPTX creation and interactive
matching features and only provides a simple fetch-and-dump command.
"""

import json
import requests
import argparse
import sys

API_URL = "https://songbase.life/api/v2/app_data?language=english"


def fetch_hymns():
    resp = requests.get(API_URL, timeout=30)
    resp.raise_for_status()
    return resp.json()


def save_songs_json(data: dict, filename: str = "songs.json"):
    """Extract songs array from the API response and write to filename as JSON."""
    songs = data.get("songs") or data.get("hymns")
    out = songs if songs is not None else data
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote {len(out) if isinstance(out, list) else 1} items to: {filename}")
    except Exception as e:
        print(f"❌ Failed to write songs to {filename}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Fetch Songbase songs and write to JSON")
    parser.add_argument("--out", "-o", default="songs.json", help="Output filename (default: songs.json)")
    args = parser.parse_args()

    print("Fetching hymn database and dumping songs...")
    try:
        data = fetch_hymns()
    except Exception as e:
        print(f"Failed to fetch hymns: {e}")
        sys.exit(1)
    save_songs_json(data, args.out)


if __name__ == "__main__":
    main()
