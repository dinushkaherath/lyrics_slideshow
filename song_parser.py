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
    
    def parse_lyrics(self, lyrics: str) -> List[Dict[str, str]]:
        """Parse lyrics into a list of stanzas and identify chorus."""
        # Split lyrics into stanzas
        stanzas = [s for s in lyrics.split('\n\n') if s.strip()]
        parsed_lyrics = []
        chorus_count = 0
        
        for stanza in stanzas:
            # Split into lines and remove empty lines
            lines = [line for line in stanza.split('\n') if line.strip()]
            if not lines:
                continue
            
            # Check if stanza is indented (chorus)
            # A stanza is a chorus if the first non-empty line starts with spaces
            first_non_empty = next(line for line in stanza.split('\n') if line.strip())
            is_chorus = first_non_empty.startswith('        ')  # 8 spaces
            
            # Process the stanza
            first_line = lines[0].strip()
            number = None
            
            # Only look for verse numbers in non-chorus sections
            if not is_chorus and first_line.startswith(('1.', '2.', '3.', '4.', '5.')):
                number = int(first_line[0])
                lines[0] = lines[0][2:].strip()
            elif is_chorus:
                chorus_count += 1
                number = chorus_count
            
            # Strip all lines and join them back together
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