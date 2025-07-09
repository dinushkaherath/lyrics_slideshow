import json
import re
import unicodedata
from difflib import SequenceMatcher
from lyrics_parser import clean_lyrics, parse_lyrics_sections

# -------------------------
# Utils
# -------------------------

def normalize(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

def similar(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def load_target_songs(filepath):
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

def sort_by_line(items):
    return sorted(items, key=lambda x: x["line_number"])

# -------------------------
# Main search function
# -------------------------

def search_songs(song_json_path, targets_txt_path):
    with open(song_json_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)
        songs = full_data["songs"]
        hymn_map = build_hymn_number_map(full_data["books"][0]["songs"])
        song_id_map = {song["id"]: song for song in songs}

    parsed_targets = load_target_songs(targets_txt_path)

    exact_matches_hymn = []
    exact_matches_title = []
    fuzzy_matches = []
    failures = []

    for target in parsed_targets:
        # 1. Hymn number match
        if target["hymn_number"] and target["hymn_number"] in hymn_map:
            song_id = hymn_map[target["hymn_number"]]
            song = song_id_map.get(song_id)
            if song:
                exact_matches_hymn.append({
                    "line_number": target["line_number"],
                    "original": target["original"],
                    "match_type": "exact match by hymn number",
                    "song_id": song["id"],
                    "title": song["title"],
                    "lyrics": song["lyrics"],
                })
                continue

        # 2. Title or lyrics match
        normalized_target = normalize(target["title"])
        found = False
        for song in songs:
            title_norm = normalize(song.get("title", ""))
            lyrics_norm = normalize(song.get("lyrics", ""))
            first_line_norm = normalize(song.get("lyrics", "").split("\n", 1)[0])

            if (normalized_target in title_norm or
                normalized_target in lyrics_norm or
                normalized_target in first_line_norm):
                exact_matches_title.append({
                    "line_number": target["line_number"],
                    "original": target["original"],
                    "match_type": "exact match by title",
                    "song_id": song["id"],
                    "title": song["title"],
                    "lyrics": song["lyrics"],
                })
                found = True
                break

        if not found:
            # 3. Fuzzy match
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
                    "lyrics": best_match["lyrics"],
                })
            else:
                failures.append({
                    "line_number": target["line_number"],
                    "original": target["original"]
                })

    return {
        "total": len(parsed_targets),
        "exact_matches_hymn": sort_by_line(exact_matches_hymn),
        "exact_matches_title": sort_by_line(exact_matches_title),
        "fuzzy_matches": sort_by_line(fuzzy_matches),
        "failures": sorted(failures, key=lambda x: x["line_number"])
    }

# -------------------------
# New function: get all lyrics in order and cleaned
# -------------------------

def get_cleaned_lyrics_tuples(result):
    combined = []
    for category in ("exact_matches_hymn", "exact_matches_title", "fuzzy_matches"):
        combined.extend(result[category])
    combined_sorted = sorted(combined, key=lambda x: x["line_number"])

    output = []
    for item in combined_sorted:
        line_number = item["line_number"]
        title = item["title"]
        lyrics = clean_lyrics(item["lyrics"])
        choruses, parsed_lyrics = parse_lyrics_sections(lyrics)
        output.append((line_number, title, choruses, parsed_lyrics))

    return output

# -------------------------
# CLI Demo (Optional)
# -------------------------

if __name__ == "__main__":
    result = search_songs("songs.json", "target_songs.txt")

    def summarize(label, symbol, items):
        count = len(items)
        percent = (count / result["total"]) * 100 if result["total"] > 0 else 0
        lines = ", ".join(str(i["line_number"]) for i in items)
        print(f"{symbol} {label}: {count}/{result['total']} ({percent:.1f}%) → songs: {lines if lines else '—'}")

    def print_block(title, emoji, matches):
        print(f"\n{emoji} {title}:\n")
        for m in matches:
            print(f"{m['line_number']:2d}. [{emoji}] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
            print(f"     Lyrics: {m['lyrics'][:100].replace(chr(10), ' ')}...\n")

    print_block("Exact Matches by Hymn Number", "✅", result["exact_matches_hymn"])
    print_block("Exact Matches by Title/Lyrics", "✅", result["exact_matches_title"])
    print_block("Fuzzy Matches (review recommended)", "🔍", result["fuzzy_matches"])

    print("\n❌ No Matches Found:\n")
    for f in result["failures"]:
        print(f"{f['line_number']:2d}. [❌] '{f['original']}' not found")

    print("\n📊 Summary:\n")
    summarize("Matched by Hymn Number", "✅", result["exact_matches_hymn"])
    summarize("Matched by Title/Lyrics", "✅", result["exact_matches_title"])
    summarize("Fuzzy Matched", "🔍", result["fuzzy_matches"])
    summarize("No Match Found", "❌", result["failures"])
