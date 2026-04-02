import re
import os
import json

from typing import List, Dict

# This can live in memory
_lyrics_version_cache = {}
CACHE_FILE = "version_choices.json"

_section_order_cache = {}
SECTION_ORDER_FILE = "section_order.json"

_section_labels_cache = {}
SECTION_LABELS_FILE = "section_labels.json"

# Load caches from disk if available
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        _lyrics_version_cache = json.load(f)

if os.path.exists(SECTION_ORDER_FILE):
    with open(SECTION_ORDER_FILE, "r", encoding="utf-8") as f:
        _section_order_cache = json.load(f)

if os.path.exists(SECTION_LABELS_FILE):
    with open(SECTION_LABELS_FILE, "r", encoding="utf-8") as f:
        _section_labels_cache = json.load(f)

def clean_lyrics(text):
    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        # Skip metadata lines: hashtags, Capo lines, and copyright notices
        if (stripped.startswith('#') or 
            stripped.lower().startswith('capo') or 
            re.match(r"^\(c\)", stripped, re.IGNORECASE)):
            continue
        # Remove chords in brackets but preserve whitespace
        cleaned_line = re.sub(r"\[.*?\]", "", line)
        cleaned_lines.append(cleaned_line.rstrip())  # preserve left spaces, trim right

    return "\n".join(cleaned_lines).strip()

def parse_lyrics_sections(text: str) -> List[Dict]:
    """
    Parses song lyrics into labeled sections as 'stanza' or 'chorus'.

    Detection Rules:
    - Lines with only a number (e.g., "1", "2") are stanza markers and signal the start of a new stanza.
    - Lines that are indented (start with 2 or more spaces) are treated as part of a chorus.
    - Empty lines signal the end of a section.

    Returns:
        List[Dict]: A list of dictionaries, each with keys:
            - 'type': 'stanza' or 'chorus'
            - 'number': the section number (incremented separately per type)
            - 'content': cleaned multiline string for the section
    """
    sections = []
    lines = text.splitlines()

    # Trackers for numbering and section content
    stanza_number = 0
    chorus_number = 0
    current_block = []  # Accumulates lines of the current section
    current_type = None  # 'stanza' or 'chorus'

    def flush_block():
        """Finalize and store the current block of lines, labeled by type."""
        nonlocal current_block, current_type, stanza_number, chorus_number
        if not current_block:
            return
        
        content = "\n".join(current_block).strip()
        if current_type == "stanza":
            stanza_number += 1
            sections.append({
                "type": "stanza",
                "number": stanza_number,
                "content": content
            })
        elif current_type == "chorus":
            chorus_number += 1
            sections.append({
                "type": "chorus",
                "number": chorus_number,
                "content": content
            })
        
        # Reset the block after storing
        current_block = []

    # Iterate through each line of the lyrics
    for line in lines:
        stripped = line.strip()

        # Detect a stanza marker (just a number)
        if re.match(r"^\d+$", stripped):
            flush_block()         # End previous section
            current_type = "stanza"
            continue              # Skip the marker itself

        # Empty line → signals section boundary
        if stripped == "":
            flush_block()
            continue

        # Check if line is indented (indicates chorus)
        is_indented = bool(re.match(r"^\s{2,}\S", line))

        # If we're starting a new section, decide type based on indentation
        if not current_block:
            current_type = "chorus" if is_indented else "stanza"

        current_block.append(line)

    flush_block()  # Final section flush at EOF
    return chorus_number, sections


def _apply_labels(sections: List[Dict], labels: Dict[str, str]) -> List[Dict]:
    """
    Apply a {str_index: label} map to sections, then renumber stanzas sequentially.
    Labels are like "S", "C1", "C2".
    """
    relabeled = []
    for i, s in enumerate(sections, 1):
        label = labels.get(str(i))
        if label:
            if label == "S":
                relabeled.append({**s, "type": "stanza"})
            elif label.startswith("C"):
                num = 1
                if len(label) > 1:
                    try:
                        num = int(label[1:])
                    except ValueError:
                        pass
                relabeled.append({**s, "type": "chorus", "number": num})
            else:
                relabeled.append(s)
        else:
            relabeled.append(s)

    # Renumber stanzas sequentially
    stanza_count = 0
    final = []
    for s in relabeled:
        if s["type"] == "stanza":
            stanza_count += 1
            final.append({**s, "number": stanza_count})
        else:
            final.append(s)
    return final


def relabel_sections(title: str, sections: List[Dict]) -> List[Dict]:
    """
    Show parsed sections and let the user reassign labels (S, C1, C2, etc.)
    when auto-detection was wrong. Caches choices to section_labels.json.
    """
    if title in _section_labels_cache:
        return _apply_labels(sections, _section_labels_cache[title])

    print(f"\n🎵 {title} — Section Labels")
    for i, s in enumerate(sections, 1):
        label = "C" + str(s["number"]) if s["type"] == "chorus" else "S" + str(s["number"])
        first_line = s["content"].splitlines()[0][:60] if s["content"] else ""
        print(f"  [{i}] {label:4}  {first_line}")

    print("\nRelabel? Enter e.g. '2=C1 4=C2 5=S' or ENTER to keep as-is:")
    raw = input("> ").strip()

    if not raw:
        labels = {}
    else:
        labels = {}
        for part in raw.split():
            if "=" not in part:
                continue
            idx_str, lbl = part.split("=", 1)
            try:
                idx = int(idx_str)
                if 1 <= idx <= len(sections):
                    labels[str(idx)] = lbl.upper()
            except ValueError:
                pass

    _section_labels_cache[title] = labels
    with open(SECTION_LABELS_FILE, "w", encoding="utf-8") as f:
        json.dump(_section_labels_cache, f, indent=2, ensure_ascii=False)

    return _apply_labels(sections, labels)


def _expand_pattern(tokens: List[str], stanzas: List[Dict], choruses_by_num: Dict) -> List[Dict]:
    """
    Expand a token pattern into a full section list.
    S = next stanza (sequential), C/C1/C2 = specific chorus.
    The pattern repeats until all stanzas are consumed.
    """
    result = []
    stanza_idx = 0
    has_s = any(t.upper() == "S" for t in tokens)

    while True:
        for token in tokens:
            upper = token.upper()
            if upper == "S":
                if stanza_idx >= len(stanzas):
                    return result
                result.append(stanzas[stanza_idx])
                stanza_idx += 1
            else:
                num = 1
                if upper.startswith("C") and len(upper) > 1:
                    try:
                        num = int(upper[1:])
                    except ValueError:
                        pass
                chorus = choruses_by_num.get(num)
                if chorus:
                    result.append(chorus)

        if not has_s:
            break  # No S tokens → pattern runs exactly once

    return result


def _default_pattern(stanzas: List[Dict], choruses: List[Dict], chorus_first: bool = False) -> str:
    """Build a compact default pattern string from the song's sections."""
    if not choruses:
        return "S"
    if len(choruses) == 1:
        # If chorus appears before the first stanza, begin and end with chorus (C1 S repeats → C S C S C)
        return "C1 S" if chorus_first else "S C1"
    if len(choruses) == 2:
        # Repeat C1 for all stanzas except the last, which gets C2
        n = len(stanzas)
        if n == 0:
            return "C1 C2"
        tokens = ["S", "C1"] * (n - 1) + ["S", "C2"]
        return " ".join(tokens)
    # 3+ choruses: alternate stanzas with each chorus in order
    tokens = []
    for i, _ in enumerate(choruses):
        tokens.append("S")
        tokens.append(f"C{i + 1}")
    return " ".join(tokens)


def arrange_sections(title: str, unique_sections: List[Dict], auto_ordered: List[Dict]) -> List[Dict]:
    """
    Let the user define section order using S/C tokens. Pattern repeats until stanzas run out.
    Caches the pattern string to section_order.json.
    """
    stanzas = [s for s in unique_sections if s["type"] == "stanza"]
    choruses = [s for s in unique_sections if s["type"] == "chorus"]
    choruses_by_num = {c["number"]: c for c in choruses}

    if title in _section_order_cache:
        pattern = _section_order_cache[title]
        tokens = pattern.split()
        result = _expand_pattern(tokens, stanzas, choruses_by_num)
        if result:
            return result

    print(f"\n🎵 {title} — Section Order")
    stanza_labels = "  ".join(f"S{s['number']}" for s in stanzas) or "none"
    chorus_labels = "  ".join(f"C{c['number']}: {c['content'].splitlines()[0][:40]}" for c in choruses) or "none"
    print(f"  Stanzas : {stanza_labels}")
    print(f"  Choruses: {chorus_labels}")
    print()
    print("  S  = next stanza (repeats through all stanzas)")
    print("  C1, C2, ... = specific chorus")
    print("  Pattern repeats until all stanzas are used")
    print()

    chorus_first = bool(unique_sections) and unique_sections[0]["type"] == "chorus"
    default = _default_pattern(stanzas, choruses, chorus_first=chorus_first)
    print(f"Default: {default}")
    print("Enter pattern (e.g. 'S C1 S C2' or 'S S C1') or ENTER for default:")
    raw = input("> ").strip()

    if not raw:
        pattern = default
    else:
        tokens = raw.upper().split()
        test = _expand_pattern(tokens, stanzas, choruses_by_num)
        if test:
            pattern = raw.upper()
        else:
            print("Pattern produced no output, using default.")
            pattern = default

    tokens = pattern.split()
    result = _expand_pattern(tokens, stanzas, choruses_by_num)

    _section_order_cache[title] = pattern
    with open(SECTION_ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(_section_order_cache, f, indent=2, ensure_ascii=False)

    return result

def choose_lyrics_version(song_title, lyrics, persist=True):
    """
    Choose a version of lyrics if multiple are found (based on '### ' headers).
    Caches user choice by song title.
    """
    headers = list(re.finditer(r'^###\s+(.+)$', lyrics, re.MULTILINE))
    
    if not headers:
        return lyrics  # No versions to choose

    if song_title in _lyrics_version_cache:
        chosen_header = _lyrics_version_cache[song_title]
        print(f"✅ Using cached version for '{song_title}': {chosen_header}")
    else:
        print(f"\n🎵 Song: {song_title}")
        print("Multiple versions detected:")
        for i, match in enumerate(headers):
            print(f"  {i + 1}. {match.group(1)}")

        while True:
            try:
                choice = int(input("Choose version number: ")) - 1
                if 0 <= choice < len(headers):
                    break
            except ValueError:
                pass
            print("Invalid choice. Try again.")

        chosen_header = headers[choice].group(1)
        _lyrics_version_cache[song_title] = chosen_header

        if persist:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(_lyrics_version_cache, f, indent=2, ensure_ascii=False)

    # Extract the selected version block
    selected_index = next(i for i, h in enumerate(headers) if h.group(1) == chosen_header)
    start = headers[selected_index].end()
    end = headers[selected_index + 1].start() if selected_index + 1 < len(headers) else len(lyrics)

    return lyrics[start:end].strip()

# Example usage:
if __name__ == "__main__":
    sample = """
1
Jesus, O living Word of God,
Wash me and cleanse me with Your blood,
So You can speak to me.
Just let me hear Your words of grace;
Just let me see Your radiant face,
Beholding constantly.

  Jesus, living Word,
  My heart thirsts for Thee.
  Of Thee I�d eat and drink,
  Enjoy Thee thoroughly.

2
Jesus, most precious One to me,
I want to seek You constantly,
So You can spread through me.
I would just call upon Your name,
Open to You; I have no shame
Loving You, Jesus Lord.

  Jesus, precious One,
  Be so real to me.
  You are all I want;
  I open wide to Thee.

3
Jesus, O living One in me,
Open my eyes that I might see
All that You are to me.
Just let me enter in Your heart;
Never from You would I depart,
Loving You constantly.

  Jesus, living One,
  Flood me thoroughly.
  Take my willing heart
  And overcome in me.

4
Lord, I want You to have Your way.
Save me from being Satan�s prey;
I am believing You.
All I can give to You, my Lord,
Is my whole being, love outpoured;
Lord, I belong to You.

  Jesus, faithful God,
  Gain us through and through.
  Use us thoroughly
  To see Your purpose through.
"""
    from pprint import pprint
    pprint(parse_lyrics_sections(sample.strip()))
