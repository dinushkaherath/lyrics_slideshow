import json
import re
import unicodedata
from difflib import SequenceMatcher

def normalize(s):
    """Normalize to lowercase ASCII, remove non-alphanum except space."""
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r"[^\w\s]", "", s)
    return s.lower().strip()

def similar(a, b):
    """Return similarity ratio between two strings."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# Load your song JSON (adjust path as needed)
with open("songs.json", "r", encoding="utf-8") as f:
    songs = json.load(f)['songs']

# Input song list
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

# Strip (Hymns, ####) from target titles
parsed_targets = []
for title in target_songs:
    match = re.match(r"^(.*?)(?:\s+\(Hymns?,?\s*\d+\))?$", title.strip())
    if match:
        parsed_title = match.group(1)
        parsed_targets.append({
            "original": title,
            "title": parsed_title
        })

# Match logic
exact_matches = []
fuzzy_matches = []
failures = []

for target in parsed_targets:
    normalized_target = normalize(target["title"])
    found = False

    for song in songs:
        title_norm = normalize(song.get("title", ""))
        lyrics_norm = normalize(song.get("lyrics", ""))
        first_line_norm = normalize(song.get("lyrics", "").split("\n", 1)[0])

        if normalized_target in title_norm or normalized_target in lyrics_norm or normalized_target in first_line_norm:
            exact_matches.append({
                "original": target["original"],
                "match_type": "exact match",
                "song_id": song["id"],
                "title": song["title"],
                "lyrics_snippet": song["lyrics"][:100].replace("\n", " ") + "..."
            })
            found = True
            break

    if not found:
        # Try fuzzy match
        best_match = None
        best_score = 0.0
        for song in songs:
            score = similar(target["title"], song.get("title", ""))
            if score > best_score:
                best_match = song
                best_score = score

        if best_score >= 0.85:
            fuzzy_matches.append({
                "original": target["original"],
                "match_type": f"fuzzy match ({best_score:.2f})",
                "song_id": best_match["id"],
                "title": best_match["title"],
                "lyrics_snippet": best_match["lyrics"][:100].replace("\n", " ") + "..."
            })
        else:
            failures.append({ "original": target["original"] })

# Output

print("\n✅ Exact Matches:\n")
for m in exact_matches:
    print(f"[✅] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
    print(f"     Lyrics: {m['lyrics_snippet']}\n")

print("\n🔍 Fuzzy Matches (review recommended):\n")
for m in fuzzy_matches:
    print(f"[🔍] '{m['original']}' → '{m['title']}' (ID: {m['song_id']}) via {m['match_type']}")
    print(f"     Lyrics: {m['lyrics_snippet']}\n")

print("\n❌ No Matches Found:\n")
for f in failures:
    print(f"[❌] '{f['original']}' not found")
