import json
import re
import unicodedata
from difflib import SequenceMatcher

# -------------------------
# Utils
# -------------------------

def normalize(s):
    """Normalize to lowercase ASCII, remove non-alphanum except space."""
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

def similar(a, b):
    """Return similarity ratio between two strings."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def load_target_songs(filepath):
    """Load and parse target song titles from a text file."""
    targets = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            match = re.match(r"^\s*(\d+)\s+(.*?)\s*$", line)
            if match:
                number = int(match.group(1))
                full_title = match.group(2)
                base_title = re.sub(r"\s+\(Hymns?,?\s*\d+\)$", "", full_title).strip()
                hymn_number_match = re.search(r"\(Hymns?,?\s*(\d+)\)", full_title)
                hymn_number = hymn_number_match.group(1) if hymn_number_match else None
                targets.append({
                    "line_number": number,
                    "original": full_title,
                    "title": base_title,
                    "hymn_number": hymn_number
                })
    return targets

def build_hymn_number_map(book_songs):
    return {v: int(k) for k, v in book_songs.items()}

# -------------------------
# Load data
# -------------------------

# Load JSON song list
with open("songs.json", "r", encoding="utf-8") as f:
    full_data = json.load(f)
    songs = full_data["songs"]
    hymn_map = build_hymn_number_map(full_data["books"][0]["songs"])
    song_id_map = {song["id"]: song for song in songs}

# Load target song list
parsed_targets = load_target_songs("target_songs.txt")

# -------------------------
# Matching Logic
# -------------------------

exact_matches = []
fuzzy_matches = []
failures = []

for target in parsed_targets:
    # 1. Try matching by hymn number first
    if target["hymn_number"] and target["hymn_number"] in hymn_map:
        song_id = hymn_map[target["hymn_number"]]
        song = song_id_map.get(song_id)
        if song:
            exact_matches.append({
                "line_number": target["line_number"],
                "original": target["original"],
                "match_type": "exact match by hymn number",
                "song_id": song["id"],
                "title": song["title"],
                "lyrics_snippet": song["lyrics"][:100].replace("\n", " ") + "..."
            })
            continue

    # 2. Try matching by title or lyrics
    normalized_target = normalize(target["title"])
    found = False
    for song in songs:
        title_norm = normalize(song.get("title", ""))
        lyrics_norm = normalize(song.get("lyrics", ""))
        first_line_norm = normalize(song.get("lyrics", "").split("\n", 1)[0])

        if (normalized_target in title_norm or
            normalized_target in lyrics_norm or
            normalized_target in first_line_norm):
            exact_matches.append({
                "line_number": target["line_number"],
                "original": target["original"],
                "match_type": "exact match by title",
                "song_id": song["id"],
                "title": song["title"],
                "lyrics_snippet": song["lyrics"][:100].replace("\n", " ") + "..."
            })
            found = True
            break

    if not found:
        # 3. Try fuzzy match
        best_match = None
        best_score = 0.0
        for song in songs:
            score = similar(target["title"], song.get("title", ""))
            if score > best_score:
                best_match = song
                best_score = score

        if best_score >= 0.85:
            fuzzy_matches.append({
                "line_number": target["line_number"],
                "original": target["original"],
                "match_type": f"fuzzy match ({best_score:.2f})",
                "song_id": best_match["id"],
                "title": best_match["title"],
                "lyrics_snippet": best_match["lyrics"][:100].replace("\n", " ") + "..."
            })
        else:
            failures.append({
                "line_number": target["line_number"],
                "original": target["original"]
            })

# -------------------------
# Output
# -------------------------

def sort_by_line(items):
    return sorted(items, key=lambda x: x["line_number"])

print("\n✅ Exact Matches:\n")
for m in sort_by_line(exact_matches):
    print(f"{m['line_number']:2d}. [✅] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
    print(f"     Lyrics: {m['lyrics_snippet']}\n")

print("\n🔍 Fuzzy Matches (review recommended):\n")
for m in sort_by_line(fuzzy_matches):
    print(f"{m['line_number']:2d}. [🔍] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
    print(f"     Lyrics: {m['lyrics_snippet']}\n")

print("\n❌ No Matches Found:\n")
for f in sorted(failures, key=lambda x: x["line_number"]):
    print(f"{f['line_number']:2d}. [❌] '{f['original']}' not found")
