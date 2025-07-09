import re

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
