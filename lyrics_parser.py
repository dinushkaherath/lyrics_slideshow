import re
from typing import List, Dict

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
