import json
import re

import unicodedata

def normalize(s):
    # Normalize to lowercase ASCII and remove non-alphanum chars except spaces
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

# Sample input
target_songs = [
    "Oh what a mystery!",
    "Never did I dream before (Hymns, 1238)",
    "I am the living bread",
    "Until we all arrive",
    "Jesus Lord, I'm captured by Thy beauty",
    "I've got a river of life",
    "Eat the bread, ye people of the Lord (Hymns, 1108)",
    "Just taste and see (Hymns, 1331)",
    "But we all, but we all with unveiled face",
    "This is the year of Jubilee!",
    "Do come, oh, do come (Hymns, 1151)",
    "Fill my spirit up",
    "I am crucified with Christ",
    "Draw me, dear Lord",
    "I'm so happy here",
    "Jesus, O living word of God",
    "Dearest Lord, You've called us here",
    "Therefore with joy (Hymns, 1340)",
    "Therefore the redeemed (Hymns, 1341)",
    "Christ is the Tree of Life",
    "'Tis the local church proclaiming (Hymns, 1096)",
    "Manna from heaven came down",
    "Christ is a genuine Man",
    "I come to Thee dear Lord (Hymns, 812)",
    "In this godless age",
    "Pursue Him and know Him",
    "Rekindle!",
    "Recall how David swore (Hymns, 1248)",
    "Growing up together in the Lord",
    "Oh, the church of Christ is glorious (Hymns, 1226)",
    "We will sing to the Lord (Hymns, 1141)",
    "O I'm a man (Hymns, 1293)",
    "Let us eat Jesus every day (Hymns, 1146)",
    "What a victory! What a triumph! (Hymns, 1174)",
    "Down from His glory (Hymns, 82)",
    "God has called us for His purpose",
    "Lord, I just love You (In my heart)",
    "Have you been to Jesus for the cleansing pow'r (Hymns, 1007)",
    "What can wash away my sin? (Hymns, 1008)",
    "Lord, keep my heart always true to you",
    "There's a man in the glory (Hymns, 505)",
    "Oh, Come see a Man",
    "Hear the Lord He's calling onward"
]

# Load the JSON song list (replace with file or API load if needed)
with open("songs.json", "r", encoding="utf-8") as f:
    songs = json.load(f)['songs']

# Preprocess target titles (extract hymn numbers where present)
parsed_targets = []
for title in target_songs:
    match = re.match(r"^(.*?)(?:\s+\(Hymns?,?\s*(\d+)\))?$", title.strip())
    if match:
        base_title = match.group(1).strip().lower()
        hymn_number = match.group(2)
        parsed_targets.append({
            "original": title,
            "title": base_title,
            "hymn_number": hymn_number
        })

# Match songs
matches = []
for target in parsed_targets:
    found = False
    for song in songs:

        target_title_normalized = normalize(target["title"])
        title_normalized = normalize(song.get("title") or "")
        lyrics_normalized = normalize(song.get("lyrics") or "")

        # Match by clean title
        if target_title_normalized in title_normalized or target_title_normalized in lyrics_normalized:
            matches.append({
                "match_type": "title or lyrics",
                "original": target["original"],
                "song_id": song["id"],
                "title": song["title"],
                "lyrics_snippet": song["lyrics"][:100].replace("\n", " ") + "..."
            })
            found = True
            break
        # Match by hymn number if provided
        if target["hymn_number"] and target["hymn_number"] in lyrics_normalized:
            matches.append({
                "match_type": "hymn number",
                "original": target["original"],
                "song_id": song["id"],
                "title": song["title"],
                "lyrics_snippet": song["lyrics"][:100].replace("\n", " ") + "..."
            })
            found = True
            break
    if not found:
        matches.append({
            "original": target["original"],
            "match_type": "not found"
        })

# Output results
for m in matches:
    if m["match_type"] == "not found":
        print(f"[❌] '{m['original']}' not found")
    else:
        print(f"[✅] Matched '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) by {m['match_type']}")
        print(f"     Lyrics: {m['lyrics_snippet']}")
