from typing import List, Dict, TypedDict

class Song(TypedDict):
    title: str
    sections: List[Dict[str, str]]

class SongParser:
    def parse_songs(self, text: str) -> List[Song]:
        """Parse multiple songs from text input."""
        # Split text into individual songs
        raw_songs = [s.strip() for s in text.split('Song') if s.strip()]
        songs = []
        
        for raw_song in raw_songs:
            # Split title and content
            lines = raw_song.split('\n', 1)
            if len(lines) < 2:
                continue
                
            title = lines[0].strip()
            if title.isdigit():  # If title is just a number, make it more descriptive
                title = f"Song {title}"
            lyrics = lines[1].strip()
            
            # Parse the lyrics into sections
            sections = self.parse_lyrics(lyrics)
            
            songs.append({
                'title': title,
                'sections': sections
            })
        
        return songs
    
    def clean_section_content(self, content: str) -> str:
        """Clean section content by removing labels and extra whitespace."""
        # Remove common labels like "Chorus 1:", "Verse 1:", etc.
        lines = content.split('\n')
        if lines and any(label in lines[0].lower() for label in ['chorus', 'verse']):
            lines = lines[1:]
        return '\n'.join(line.strip() for line in lines if line.strip())

    def parse_lyrics(self, lyrics: str) -> List[Dict[str, str]]:
        """Parse lyrics into a list of stanzas and identify chorus."""
        # Split lyrics into stanzas
        stanzas = [s for s in lyrics.split('\n\n') if s.strip()]
        parsed_lyrics = []
        chorus_count = 0
        verse_count = 0
        
        for stanza in stanzas:
            # Split into lines and remove empty lines
            lines = [line for line in stanza.split('\n') if line.strip()]
            if not lines:
                continue
            
            # Get the first non-empty line for analysis
            first_non_empty = next(line for line in stanza.split('\n') if line.strip())
            
            # Check various chorus indicators
            is_chorus = (
                first_non_empty.startswith('        ') or  # 8 spaces indentation
                first_non_empty.lower().startswith('chorus') or
                'chorus' in first_non_empty.lower()
            )
            
            # Clean up the content
            content = self.clean_section_content(stanza)
            lines = content.split('\n')
            
            number = None
            # Handle verse numbering
            if not is_chorus:
                verse_count += 1
                if lines and any(lines[0].startswith(f"{i}.") for i in range(1, 10)):
                    # Extract number if it exists
                    number = int(lines[0][0])
                    lines[0] = lines[0][2:].strip()
                else:
                    # For unnumbered verses, use the verse count
                    number = verse_count
            else:
                chorus_count += 1
                number = chorus_count
            
            # Join the cleaned lines
            content = '\n'.join(line.strip() for line in lines)
            
            # Create the section
            section = {
                'type': 'chorus' if is_chorus else 'verse',
                'content': content,
                'number': number
            }
            
            parsed_lyrics.append(section)
        
        return parsed_lyrics

def main():
    # Example usage
    parser = SongParser()
    
    # Read songs from a file
    with open('songs.txt', 'r') as f:
        songs_text = f.read()
    
    # Parse songs
    songs = parser.parse_songs(songs_text)
    
    # Print parsed structure
    for song in songs:
        print(f"\nTitle: {song['title']}")
        for section in song['sections']:
            section_type = section['type']
            number = f" {section['number']}" if section['number'] is not None else ""
            print(f"\n{section_type.capitalize()}{number}:")
            print(section['content'])

if __name__ == '__main__':
    main() 