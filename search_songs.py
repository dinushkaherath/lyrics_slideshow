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
    """Load previously saved song selections (cache) from disk."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_saved_choices(cache):
    """Write updated selections (cache) to disk."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def normalize(s):
    """Normalize string for comparison."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

def similar(a, b):
    """Calculate similarity ratio between two normalized strings."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def sort_by_line(items):
    """Sort list of dictionaries by 'line_number' key."""
    return sorted(items, key=lambda x: x["line_number"])

def build_hymn_number_map(book_songs):
    """Build a mapping from hymn number (string) to song ID (int)."""
    # Assuming book_songs is a dictionary {hymn_number: song_id}
    return {v: int(k) for k, v in book_songs.items()}

# -------------------------
# Data Loading and Parsing
# -------------------------

def load_target_songs(filepath):
    """Loads target songs from a text file and extracts title/hymn number."""
    targets = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            # Case 1: line only digits → hymn number
            if re.fullmatch(r"\d+", line):
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": "", "hymn_number": line
                })
                continue

            # Case 2: line with number and title (e.g. "512 God is Good")
            match_both = re.match(r"^(\d+)\s+(.+)$", line)
            if match_both:
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": match_both.group(2).strip(), "hymn_number": match_both.group(1)
                })
                continue

            # Case 3: title with "(Hymn 123)"
            match_paren = re.match(r"^(.*?)\s*\(Hymns?,?\s*(\d+)\)\s*$", line)
            if match_paren:
                targets.append({
                    "line_number": line_number, "original": line,
                    "title": match_paren.group(1).strip(), "hymn_number": match_paren.group(2)
                })
                continue

            # Case 4: just a plain title
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
    Matches input target songs (by hymn number or title/lyrics) against the full song library.
    Returns results categorized into exact matches, fuzzy matches (candidates), and failures.
    """
    with open(song_json_path, "r", encoding="utf-8") as f:
        full_data = json.load(f)
        songs = full_data["songs"]
        # Assumes the first book in the list provides the hymn number mapping
        hymn_map = build_hymn_number_map(full_data["books"][0]["songs"])
        song_id_map = {song["id"]: song for song in songs}

    parsed_targets = load_target_songs(targets_txt_path)
    matched_song_ids = set()

    exact_matches_hymn = []
    exact_matches_title = []
    fuzzy_matches = []
    failures = []

    for target in parsed_targets:
        # 1. Hymn number match
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

        # 2. Title / lyrics match
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

            if len(title_matches) == 1:
                song = title_matches[0]
                exact_matches_title.append({
                    "line_number": target["line_number"], "original": target["original"],
                    "match_type": "exact match by title", "song_id": song["id"],
                    "title": song["title"], "lyrics": song["lyrics"],
                })
                matched_song_ids.add(song["id"])
                continue

            elif len(title_matches) > 1:
                fuzzy_matches.append({
                    "line_number": target["line_number"], "original": target["original"],
                    "match_type": f"multiple title matches ({len(title_matches)})",
                    "candidates": [
                        {
                            "song_id": s["id"], "title": s["title"],
                            "lyrics": s["lyrics"]
                        } for s in title_matches
                    ]
                })
                continue

            # 3. Fuzzy fallback
            best_match = None
            best_score = 0.0
            for song in songs:
                if song["id"] in matched_song_ids: continue
                score = similar(target["title"], song.get("title", ""))
                if score > best_score:
                    best_match = song
                    best_score = score

            if best_score >= 0.80 and best_match and best_match["id"] not in matched_song_ids:
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
    Attempts to resolve multi-candidate fuzzy matches using a cache of previous choices.
    This function contains interactive prompts intended for a CLI environment.
    """
    saved_choices = load_saved_choices()

    resolved = []
    cache_updated = False

    for match in result["fuzzy_matches"]:
        # If already resolved (e.g., by fuzzy score threshold)
        if "candidates" not in match:
            resolved.append(match)
            continue

        # Try to reuse previous manual choice
        cache_key = normalize(match["original"])
        if cache_key in saved_choices:
            chosen_id = saved_choices[cache_key]
            # NOTE: Candidate lyrics are snippets, in a real system you'd fetch full lyrics here
            candidate = next((c for c in match["candidates"] if c["song_id"] == chosen_id), None)
            if candidate:
                print(f"🔁 Reusing saved choice: '{candidate['title']}' for '{match['original']}'")
                resolved.append({
                    "line_number": match["line_number"], "original": match["original"],
                    "match_type": "cached selection", "song_id": candidate["song_id"],
                    "title": candidate["title"], "lyrics": candidate["lyrics"],
                })
                continue

        # Otherwise prompt the user (This section is interactive and will halt/fail in non-CLI environments)
        print(f"\n🔍 Target: {match['original']} ({match['match_type']})\n")
        for idx, c in enumerate(match["candidates"], 1):
            print(f"  [{idx}] {c['title']} (ID: {c['song_id']})")
            snippet = c['lyrics'][:120].replace("\n", " ") + "..."
            print(f"{'-'*50}\n{snippet}\n{'-'*50}\n")

        # The interactive input logic relies on the full lyrics being available for selection
        # and is kept for completeness in a CLI script, even if non-functional in this environment.
        try:
            while True:
                choice = int(input(f"Select the correct song [1-{len(match['candidates'])}]: "))
                if 1 <= choice <= len(match["candidates"]):
                    break
                print("Invalid number. Try again.")
        except (ValueError, EOFError):
            print("\nNon-interactive environment detected or input error. Skipping resolution for this fuzzy match.")
            continue # Skip to the next match if input fails

        chosen_song = match["candidates"][choice - 1]
        print(f"✅ Selected: {chosen_song['title']}\n")

        # Save this choice in cache
        saved_choices[cache_key] = chosen_song["song_id"]
        cache_updated = True

        resolved.append({
            "line_number": match["line_number"], "original": match["original"],
            "match_type": "manual selection", "song_id": chosen_song["song_id"],
            "title": chosen_song["title"], "lyrics": chosen_song["lyrics"],
        })

    # Persist any new data
    if cache_updated:
        save_saved_choices(saved_choices)
        print(f"\n💾 Saved {len(saved_choices)} selections to {CACHE_FILE}")

    result["fuzzy_matches"] = resolved
    return result

def structure_matched_lyrics(result, repeat_choruses=True):
    """
    Takes the categorized match results, combines them, sorts by line number,
    cleans the lyrics, parses them into sections, and adds repeated choruses.
    """
    combined = []
    for category in ("exact_matches_hymn", "exact_matches_title", "fuzzy_matches"):
        combined.extend(result[category])
    combined_sorted = sorted(combined, key=lambda x: x["line_number"])

    output = []
    for item in combined_sorted:
        # Skip items that were fuzzy matches but remain unresolved (missing the full 'lyrics' key)
        if "lyrics" not in item:
            print(f"🚫 Skipping line {item.get('line_number', '?')}: Unresolved match for '{item.get('original', 'Unknown')}'")
            continue

        line_number = item["line_number"]
        title = item["title"]
        lyrics_raw = item["lyrics"]

        # 1. Process lyrics using external parser functions
        lyrics_chosen = choose_lyrics_version(title, lyrics_raw)
        lyrics = clean_lyrics(lyrics_chosen)
        num_choruses, parsed_lyrics = parse_lyrics_sections(lyrics)

        # 2. Handle repeated choruses
        lyrics_to_output = parsed_lyrics
        if repeat_choruses and num_choruses == 1:
            lyrics_with_repeated_chorus = []
            chorus_section = None
            for section in parsed_lyrics:
                lyrics_with_repeated_chorus.append(section)
                if section["type"] == "chorus":
                    chorus_section = section
                elif section["type"] == "stanza" and chorus_section:
                    # Insert chorus after every stanza
                    lyrics_with_repeated_chorus.append(chorus_section)
            lyrics_to_output = lyrics_with_repeated_chorus

        output.append((line_number, title, num_choruses, lyrics_to_output))

        if num_choruses > 1:
            print(f"⚠️  Song '{title}' has {num_choruses} choruses! (Compilation may be complex)")

    return output

# -------------------------
# Orchestration and Reporting
# -------------------------

def match_and_compile_songs(song_json_path, targets_txt_path, repeat_choruses=True):
    """
    Executes the full pipeline: match, resolve, structure, and report.
    """
    print("--- 1. Matching Target Songs to Library ---")
    match_results = match_targets_to_library(song_json_path, targets_txt_path)

    print("\n--- 2. Interactive Fuzzy Match Resolution ---")
    # Note: This step requires manual CLI input to fully resolve multi-candidate matches
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