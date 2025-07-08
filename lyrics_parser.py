import re

def clean_lyrics(text):
    cleaned_lines = []
    for line in text.splitlines():
        # Skip lines that start with a hashtag
        if line.lstrip().startswith('#'):
            continue
        # Remove chords in brackets but preserve whitespace
        cleaned_line = re.sub(r"\[.*?\]", "", line)
        cleaned_lines.append(cleaned_line.rstrip())  # preserve left spaces, trim right

    return "\n".join(cleaned_lines).strip()
