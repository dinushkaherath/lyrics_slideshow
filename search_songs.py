import json
import os
import re
import unicodedata
from difflib import SequenceMatcher
from lyrics_parser import choose_lyrics_version, clean_lyrics, parse_lyrics_sections

# -------------------------
# Utility Functions
# -------------------------

CACHE_FILE = "selected_songs.json"

def load_saved_choices():
    """Load the local JSON cache to skip re-asking about previously resolved songs."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_saved_choices(cache):
    """Write user selections to disk to persist display titles and song IDs."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def normalize(s):
    """Strip accents, punctuation, and casing to make string comparisons 'fuzzy' and robust."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

def similar(a, b):
    """Return a 0.0 to 1.0 score of how similar two strings are (Levenshtein-based)."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def sort_by_line(items):
    """Ensure results appear in the same order they were written in the input file."""
    return sorted(items, key=lambda x: x["line_number"])

def build_hymn_number_map(book_songs):
    """Convert the library's book structure into a fast lookup: { 'HymnNumber': SongID }."""
    return {v: int(k) for k, v in book_songs.items()}

# -------------------------
# Data Loading and Parsing
# -------------------------

def load_target_songs(filepath):
    """
    Reads target_songs.txt and uses Regex to identify the song title and hymn number.
    It handles formats like: '123', '123 Title', 'Title (Hymn 123)', and 'Title 123'.
    """
    targets = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            # Case 1: Pure digits (e.g., '1232')
            if re.fullmatch(r"\d+", line):
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": "", "hymn_number": line
                })
                continue

            # Case 2: Number followed by title (e.g. '1232 Jesus is Getting...')
            match_both = re.match(r"^(\d+)\s+(.+)$", line)
            if match_both:
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": match_both.group(2).strip(), "hymn_number": match_both.group(1)
                })
                continue

            # Case 3: Title followed by hymn in parentheses (e.g. 'Amazing Grace (Hymn 12)')
            match_paren = re.match(r"^(.*?)\s*\(Hymns?,?\s*(\d+)\)\s*$", line)
            if match_paren:
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": match_paren.group(1).strip(), "hymn_number": match_paren.group(2)
                })
                continue
            
            # Case 3.5: Title followed by a number at the very end (e.g. 'Praise Him 1232')
            match_end_num = re.match(r"^(.*?)\s+(\d+)$", line)
            if match_end_num:
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": match_end_num.group(1).strip(), "hymn_number": match_end_num.group(2)
                })
                continue

            # Case 4: Pure text title (no hymn number detected)
            targets.append({
                "line_number": line_number, "original": line,
                "title": line, "hymn_number": ""
            })

    return targets

# -------------------------
# Core Pipeline Steps
# -------------------------

def match_targets_to_library(song_json_path, targets_txt_path):
    """
    The 'Search Engine'. Compares input songs against songs.json in 3 stages:
    1. Direct Hymn Number lookup.
    2. Substring matching in titles/lyrics.
    3. Fuzzy score comparison for typos.
    """
    with open(song_json_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)
        songs = full_data["songs"]
        # Assumes the first book in the list provides the hymn number mapping
        hymn_map = build_hymn_number_map(full_data["books"][0]["songs"])
        song_id_map = {song["id"]: song for song in songs}

    parsed_targets = load_target_songs(targets_txt_path)
    matched_song_ids = set() # Prevent the same song from being picked twice in one run

    exact_matches_hymn = []
    exact_matches_title = []
    fuzzy_matches = []
    failures = []

    for target in parsed_targets:
        # STAGE 1: Match by Hymn Number (Highest Confidence)
        if target["hymn_number"] and target["hymn_number"] in hymn_map:
            song_id = hymn_map[target["hymn_number"]]
            if song_id not in matched_song_ids:
                song = song_id_map.get(song_id)
                if song:
                    exact_matches_hymn.append({
                        "line_number": target["line_number"], "original": target["original"],
                        "match_type": "exact match by hymn number", "song_id": song["id"],
                        "title": song["title"], "lyrics": song["lyrics"],
                    })
                    matched_song_ids.add(song_id)
                    continue

        # STAGE 2: Match by Title/Lyrics Substrings
        if target["title"]:
            normalized_target = normalize(target["title"])
            title_matches = []

            for song in songs:
                if song["id"] in matched_song_ids: continue

                title_norm = normalize(song.get("title", ""))
                lyrics_norm = normalize(song.get("lyrics", ""))
                first_line_norm = normalize(song.get("lyrics", "").split("\n", 1)[0])

                if (normalized_target in title_norm or
                    normalized_target in lyrics_norm or
                    normalized_target in first_line_norm):
                    title_matches.append(song)

            # If only one song matches the text, we call it an exact match
            if len(title_matches) == 1:
                song = title_matches[0]
                exact_matches_title.append({
                    "line_number": target["line_number"], "original": target["original"],
                    "match_type": "exact match by title", "song_id": song["id"],
                    "title": song["title"], "lyrics": song["lyrics"],
                })
                matched_song_ids.add(song["id"])
                continue

            # If multiple songs match, we save them for Step 2 resolution
            elif len(title_matches) > 1:
                fuzzy_matches.append({
                    "line_number": target["line_number"], "original": target["original"],
                    "match_type": f"multiple title matches ({len(title_matches)})",
                    "candidates": [
                        {"song_id": s["id"], "title": s["title"], "lyrics": s["lyrics"]} 
                        for s in title_matches
                    ]
                })
                continue

            # STAGE 3: Fuzzy Fallback (Typos)
            best_match = None
            best_score = 0.0
            for song in songs:
                if song["id"] in matched_song_ids: continue
                score = similar(target["title"], song.get("title", ""))
                if score > best_score:
                    best_match = song
                    best_score = score

            if best_score >= 0.80 and best_match:
                fuzzy_matches.append({
                    "line_number": target["line_number"], "original": target["original"],
                    "match_type": f"fuzzy match ({best_score:.2f})", "song_id": best_match["id"],
                    "title": best_match["title"], "lyrics": best_match["lyrics"],
                })
                matched_song_ids.add(best_match["id"])
            else:
                failures.append({"line_number": target["line_number"], "original": target["original"]})
        else:
            failures.append({"line_number": target["line_number"], "original": target["original"]})

    return {
        "total": len(parsed_targets),
        "exact_matches_hymn": sort_by_line(exact_matches_hymn),
        "exact_matches_title": sort_by_line(exact_matches_title),
        "fuzzy_matches": sort_by_line(fuzzy_matches),
        "failures": sorted(failures, key=lambda x: x["line_number"])
    }

def resolve_fuzzy_matches(result):
    """
    The 'Interactive Resolver'.
    1. Checks if the song was already chosen in a previous run.
    2. If not, asks the user to pick the correct song from candidates.
    3. Asks the user how the title should look in the final PowerPoint.
    """
    saved_choices = load_saved_choices()
    resolved = []
    cache_updated = False

    all_matches = result["exact_matches_hymn"] + result["exact_matches_title"] + result["fuzzy_matches"]

    for match in all_matches:
        cache_key = normalize(match["original"])
        
        # Check Cache
        if cache_key in saved_choices:
            saved = saved_choices[cache_key]
            match.update({
                "title": saved["display_title"],
                "song_id": saved["song_id"],
                "match_type": "cached selection"
            })
            resolved.append(match)
            continue

        print(f"\n🔍 Target: '{match['original']}'")
        
        # --- SUB-STEP A: Resolve ID (If multiple choices) ---
        chosen_song = None
        candidates = match.get("candidates", [])

        if candidates:
            print(f"Multiple matches found. Please select the correct song:")
            for idx, c in enumerate(candidates, 1):
                # Clean lyrics snippet to show user (strip chords/tags)
                snippet = re.sub(r'\[.*?\]', '', c.get('lyrics', ''))[:80].replace('\n', ' ')
                print(f"  [{idx}] {c['title']} (ID: {c['song_id']})")
                print(f"      {snippet}...")
                print()
            
            while True:
                c_choice = input(f"Select song [1-{len(candidates)}]: ").strip()
                if c_choice.isdigit() and 1 <= int(c_choice) <= len(candidates):
                    chosen_song = candidates[int(c_choice)-1]
                    break
                print("Invalid selection.")
        else:
            # Single match found, use it directly
            chosen_song = {
                "song_id": match.get("song_id"),
                "title": match.get("title"),
                "lyrics": match.get("lyrics")
            }

        # --- SUB-STEP B: Resolve Display Name ---
        print(f"\nChosen Song: {chosen_song['title']}")
        print(f"How should the title appear in the slideshow?")
        print(f"  [1] Use Library Title: '{chosen_song['title']}'")
        print(f"  [O] Use Original Input: '{match['original']}'")
        print(f"  [M] Enter Manually")

        t_choice = input("Select title option (1/O/M): ").strip().upper()

        final_title = ""
        if t_choice == 'O':
            final_title = match["original"]
        elif t_choice == 'M':
            final_title = input("Enter custom title: ").strip()
        else:
            final_title = match["original"]

        # Update the object and the persistent cache
        match.update({
            "title": final_title,
            "song_id": chosen_song["song_id"],
            "lyrics": chosen_song.get("lyrics", match.get("lyrics")),
            "match_type": "manual resolution"
        })
        
        saved_choices[cache_key] = {
            "song_id": chosen_song["song_id"],
            "display_title": final_title
        }
        cache_updated = True
        resolved.append(match)

    if cache_updated:
        save_saved_choices(saved_choices)
    
    # Consolidate everything into fuzzy_matches for the next stage
    result["fuzzy_matches"] = resolved
    result["exact_matches_hymn"] = []
    result["exact_matches_title"] = []
    
    return result

def structure_matched_lyrics(result, repeat_choruses=True):
    """
    Final data processing before PowerPoint generation.
    - Cleans chords/tags from lyrics.
    - Breaks lyrics into 'stanza' and 'chorus' objects.
    - If a song has one chorus, repeats it after every stanza.
    """
    combined = []
    for category in ("exact_matches_hymn", "exact_matches_title", "fuzzy_matches"):
        combined.extend(result[category])
    combined_sorted = sorted(combined, key=lambda x: x["line_number"])

    output = []
    for item in combined_sorted:
        if "lyrics" not in item:
            print(f"🚫 Skipping line {item.get('line_number', '?')}: Unresolved match for '{item.get('original', 'Unknown')}'")
            continue

        line_number = item["line_number"]
        title = item["title"]
        lyrics_raw = item["lyrics"]

        # Parse raw string into structured list of sections
        lyrics_chosen = choose_lyrics_version(title, lyrics_raw)
        lyrics = clean_lyrics(lyrics_chosen)
        num_choruses, parsed_lyrics = parse_lyrics_sections(lyrics)

        # Handle automatic chorus repetition logic
        lyrics_to_output = parsed_lyrics
        if repeat_choruses and num_choruses == 1:
            lyrics_with_repeated_chorus = []
            chorus_section = None
            for section in parsed_lyrics:
                lyrics_with_repeated_chorus.append(section)
                if section["type"] == "chorus":
                    chorus_section = section
                elif section["type"] == "stanza" and chorus_section:
                    lyrics_with_repeated_chorus.append(chorus_section)
            lyrics_to_output = lyrics_with_repeated_chorus

        output.append((line_number, title, num_choruses, lyrics_to_output))

    return output

# -------------------------
# Orchestration and Reporting
# -------------------------

def match_and_compile_songs(song_json_path, targets_txt_path, repeat_choruses=True):
    """Orchestrates the entire process from matching to final structuring."""
    print("--- 1. Matching Target Songs to Library ---")
    match_results = match_targets_to_library(song_json_path, targets_txt_path)

    print("\n--- 2. Interactive Fuzzy Match Resolution ---")
    resolved_results = resolve_fuzzy_matches(match_results)

    print("\n--- 3. Structuring Matched Lyrics ---")
    compiled_lyrics = structure_matched_lyrics(resolved_results, repeat_choruses=repeat_choruses)
    print(f"Successfully compiled and structured lyrics for {len(compiled_lyrics)} songs.")

    return resolved_results, compiled_lyrics

def summarize(label, symbol, items, total):
    """Prints summary statistics for a match category."""
    count = len(items)
    percent = (count / total) * 100 if total > 0 else 0
    lines = ", ".join(str(i["line_number"]) for i in items)
    print(f"{symbol} {label}: {count}/{total} ({percent:.1f}%) → lines: {lines if lines else '—'}")

def print_block(title, emoji, matches):
    """Prints a detailed block of matched results."""
    print(f"\n{emoji} {title}:\n")
    for m in matches:
        if "title" not in m:
            print(f"{m['line_number']:2d}. [{emoji}] '{m['original']}' → ⚠️ unresolved candidates ({len(m.get('candidates', []))})")
            continue
        print(f"{m['line_number']:2d}. [{emoji}] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
        # Use .get() to safely access lyrics, which may be missing in unresolved matches
        lyrics_snippet = m.get('lyrics', 'No lyrics data').replace(chr(10), ' ')[:100]
        print(f"     Lyrics: {lyrics_snippet}...\n")


# -------------------------
# CLI Entry
# -------------------------

if __name__ == "__main__":
    # --- Execute Full Pipeline ---
    match_results, compiled_lyrics = match_and_compile_songs("songs.json", "target_songs.txt")

    # --- Print Detailed Results ---
    print("\n" + "="*50)
    print("FINAL DETAILED RESULTS")
    print("="*50)
    
    print_block("Exact Matches by Hymn Number", "✅", match_results["exact_matches_hymn"])
    print_block("Exact Matches by Title/Lyrics", "✅", match_results["exact_matches_title"])
    print_block("Resolved Fuzzy Matches", "🔍", match_results["fuzzy_matches"])

    print("\n❌ No Matches Found:\n")
    for f in match_results["failures"]:
        print(f"{f['line_number']:2d}. [❌] '{f['original']}' not found")

    # --- Print Summary Totals ---
    print("\n📊 Summary Totals:\n")
    total = match_results["total"]
    summarize("Matched by Hymn Number", "✅", match_results["exact_matches_hymn"], total)
    summarize("Matched by Title/Lyrics", "✅", match_results["exact_matches_title"], total)
    summarize("Resolved Fuzzy Matches", "🔍", match_results["fuzzy_matches"], total)
    summarize("No Match Found", "❌", match_results["failures"], total)

    # --- Example of Compiled Output ---
    print("\n--- Compiled Lyrics Output (First 3) ---")
    for line_number, title, num_choruses, sections in compiled_lyrics[:3]:
        print(f"Line {line_number}: {title} (Choruses: {num_choruses}, Sections: {len(sections)})")