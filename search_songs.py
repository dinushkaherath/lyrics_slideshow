import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from lyrics_parser import choose_lyrics_version, clean_lyrics, parse_lyrics_sections

# -------------------------
# Utils
# -------------------------

CACHE_FILE = "selected_songs.json"

def load_saved_choices():
    """Load previously saved song selections from disk."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_saved_choices(cache):
    """Write updated selections to disk."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def normalize(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

def similar(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def sort_by_line(items):
    return sorted(items, key=lambda x: x["line_number"])

def build_hymn_number_map(book_songs):
    return {v: int(k) for k, v in book_songs.items()}

# -------------------------
# Target Songs Loader
# -------------------------

def load_target_songs(filepath):
    """
    Loads target songs file.
    Handles lines like:
        512
        god is good
    or:
        512 god is good
    or:
        God is Good (Hymn 512)
    Each line is treated separately.
    """
    targets = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            # Case 1: line only digits → hymn number
            if re.fullmatch(r"\d+", line):
                targets.append({
                    "line_number": line_number,
                    "original": line,
                    "title": "",
                    "hymn_number": line
                })
                continue

            # Case 2: line with number and title (e.g. "512 God is Good")
            match_both = re.match(r"^(\d+)\s+(.+)$", line)
            if match_both:
                targets.append({
                    "line_number": line_number,
                    "original": line,
                    "title": match_both.group(2).strip(),
                    "hymn_number": match_both.group(1)
                })
                continue

            # Case 3: title with "(Hymn 123)"
            match_paren = re.match(r"^(.*?)\s*\(Hymns?,?\s*(\d+)\)\s*$", line)
            if match_paren:
                targets.append({
                    "line_number": line_number,
                    "original": line,
                    "title": match_paren.group(1).strip(),
                    "hymn_number": match_paren.group(2)
                })
                continue

            # Case 4: just a plain title
            targets.append({
                "line_number": line_number,
                "original": line,
                "title": line,
                "hymn_number": ""
            })

    return targets

# -------------------------
# Main Search
# -------------------------

def search_songs(song_json_path, targets_txt_path):
    with open(song_json_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)
        songs = full_data["songs"]
        hymn_map = build_hymn_number_map(full_data["books"][0]["songs"])
        song_id_map = {song["id"]: song for song in songs}

    parsed_targets = load_target_songs(targets_txt_path)
    matched_song_ids = set()

    exact_matches_hymn = []
    exact_matches_title = []
    fuzzy_matches = []
    failures = []

    for target in parsed_targets:
        # Hymn number match
        if target["hymn_number"] and target["hymn_number"] in hymn_map:
            song_id = hymn_map[target["hymn_number"]]
            if song_id not in matched_song_ids:
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
                    matched_song_ids.add(song_id)
                    continue

        # Title / lyrics match
        if target["title"]:
            normalized_target = normalize(target["title"])
            title_matches = []

            for song in songs:
                if song["id"] in matched_song_ids:
                    continue

                title_norm = normalize(song.get("title", ""))
                lyrics_norm = normalize(song.get("lyrics", ""))
                first_line_norm = normalize(song.get("lyrics", "").split("\n", 1)[0])

                if (normalized_target in title_norm or
                    normalized_target in lyrics_norm or
                    normalized_target in first_line_norm):
                    title_matches.append(song)

            if len(title_matches) == 1:
                song = title_matches[0]
                exact_matches_title.append({
                    "line_number": target["line_number"],
                    "original": target["original"],
                    "match_type": "exact match by title",
                    "song_id": song["id"],
                    "title": song["title"],
                    "lyrics": song["lyrics"],
                })
                matched_song_ids.add(song["id"])
                continue

            elif len(title_matches) > 1:
                fuzzy_matches.append({
                    "line_number": target["line_number"],
                    "original": target["original"],
                    "match_type": f"multiple title matches ({len(title_matches)})",
                    "candidates": [
                        {
                            "song_id": s["id"],
                            "title": s["title"],
                            "lyrics": s["lyrics"][:120].replace("\n", " ") + "..."
                        } for s in title_matches
                    ]
                })
                continue

            # Fuzzy fallback
            best_match = None
            best_score = 0.0
            for song in songs:
                score = similar(target["title"], song.get("title", ""))
                if score > best_score:
                    best_match = song
                    best_score = score

            if best_score >= 0.80:
                fuzzy_matches.append({
                    "line_number": target["line_number"],
                    "original": target["original"],
                    "match_type": f"fuzzy match ({best_score:.2f})",
                    "song_id": best_match["id"],
                    "title": best_match["title"],
                    "lyrics": best_match["lyrics"],
                })
                matched_song_ids.add(best_match["id"])
            else:
                failures.append({
                    "line_number": target["line_number"],
                    "original": target["original"]
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
# Interactive Resolution (no skipping)
# -------------------------

def resolve_fuzzy_matches_and_merge(result):
    saved_choices = load_saved_choices()

    resolved = []
    cache_updated = False

    for match in result["fuzzy_matches"]:
        # Skip if this fuzzy match was already automatically resolved
        if "candidates" not in match:
            resolved.append(match)
            continue

        # Try to reuse previous manual choice
        cache_key = normalize(match["original"])
        if cache_key in saved_choices:
            chosen_id = saved_choices[cache_key]
            candidate = next((c for c in match["candidates"] if c["song_id"] == chosen_id), None)
            if candidate:
                print(f"🔁 Reusing saved choice: '{candidate['title']}' for '{match['original']}'")
                resolved.append({
                    "line_number": match["line_number"],
                    "original": match["original"],
                    "match_type": "cached selection",
                    "song_id": candidate["song_id"],
                    "title": candidate["title"],
                    "lyrics": candidate["lyrics"],
                })
                continue

        # Otherwise prompt the user
        print(f"\n🔍 Target: {match['original']} ({match['match_type']})\n")
        for idx, c in enumerate(match["candidates"], 1):
            print(f"  [{idx}] {c['title']} (ID: {c['song_id']})")
            print(f"{'-'*50}\n{c['lyrics'][:500]}\n{'-'*50}\n")

        # Force user to pick one (no skipping)
        while True:
            try:
                choice = int(input(f"Select the correct song [1-{len(match['candidates'])}]: "))
                if 1 <= choice <= len(match["candidates"]):
                    break
                print("Invalid number. Try again.")
            except ValueError:
                print("Please enter a valid number.")

        chosen_song = match["candidates"][choice - 1]
        print(f"✅ Selected: {chosen_song['title']}\n")

        # Save this choice in cache
        saved_choices[cache_key] = chosen_song["song_id"]
        cache_updated = True

        resolved.append({
            "line_number": match["line_number"],
            "original": match["original"],
            "match_type": "manual selection",
            "song_id": chosen_song["song_id"],
            "title": chosen_song["title"],
            "lyrics": chosen_song["lyrics"],
        })

    # Persist any new data
    if cache_updated:
        save_saved_choices(saved_choices)
        print(f"\n💾 Saved {len(saved_choices)} selections to {CACHE_FILE}")

    # Replace fuzzy matches with finalized ones
    result["fuzzy_matches"] = resolved
    return result

# -------------------------
# Lyrics Compilation
# -------------------------

def compile_lyrics_tuples(result, repeat_choruses=True):
    combined = []
    for category in ("exact_matches_hymn", "exact_matches_title", "fuzzy_matches"):
        combined.extend(result[category])
    combined_sorted = sorted(combined, key=lambda x: x["line_number"])

    output = []
    for item in combined_sorted:
        line_number = item["line_number"]
        title = item["title"]
        lyrics_raw = item["lyrics"]
        lyrics_chosen = choose_lyrics_version(title, lyrics_raw)
        lyrics = clean_lyrics(lyrics_chosen)
        num_choruses, parsed_lyrics = parse_lyrics_sections(lyrics)
        lyrics_with_repeated_chorus = []
        if repeat_choruses and num_choruses == 1:
            chorus_section = None
            for section in parsed_lyrics:
                lyrics_with_repeated_chorus.append(section)
                if section["type"] == "chorus":
                    chorus_section = section
                elif section["type"] == "stanza" and chorus_section:
                    lyrics_with_repeated_chorus.append(chorus_section)
            output.append((line_number, title, num_choruses, lyrics_with_repeated_chorus))
        else:
            output.append((line_number, title, num_choruses, parsed_lyrics))
        if num_choruses > 1:
            print(f"⚠️  Song '{title}' has {num_choruses} choruses!")

    return output


# ------------------------------------------------------
# 1️⃣ Diagnostic printout
# ------------------------------------------------------

def summarize(label, symbol, items):
    count = len(items)
    percent = (count / result["total"]) * 100 if result["total"] > 0 else 0
    lines = ", ".join(str(i["line_number"]) for i in items)
    print(f"{symbol} {label}: {count}/{result['total']} ({percent:.1f}%) → songs: {lines if lines else '—'}")

def print_block(title, emoji, matches):
    print(f"\n{emoji} {title}:\n")
    for m in matches:
        if "title" not in m:
            # Candidate-style fuzzy matches (should not exist anymore)
            print(f"{m['line_number']:2d}. [{emoji}] '{m['original']}' → ⚠️ unresolved candidates ({len(m.get('candidates', []))})")
            continue
        print(f"{m['line_number']:2d}. [{emoji}] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
        print(f"     Lyrics: {m['lyrics'][:100].replace(chr(10), ' ')}...\n")

# -------------------------
# CLI Entry
# -------------------------

if __name__ == "__main__":
    result = search_songs("songs.json", "target_songs.txt")

    print("\n--- Interactive Fuzzy Match Resolution ---")
    result = resolve_fuzzy_matches_and_merge(result)

    print_block("Exact Matches by Hymn Number", "✅", result["exact_matches_hymn"])
    print_block("Exact Matches by Title/Lyrics", "✅", result["exact_matches_title"])
    print_block("Resolved Fuzzy Matches", "🔍", result["fuzzy_matches"])

    # ------------------------------------------------------
    # 3️⃣ Summary totals
    # ------------------------------------------------------

    print("\n📊 Summary:\n")
    summarize("Matched by Hymn Number", "✅", result["exact_matches_hymn"])
    summarize("Matched by Title/Lyrics", "✅", result["exact_matches_title"])
    summarize("Resolved Fuzzy Matches", "🔍", result["fuzzy_matches"])
    summarize("No Match Found", "❌", result["failures"])
