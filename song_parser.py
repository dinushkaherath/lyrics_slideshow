from typing import List, Dict, TypedDict

class Song(TypedDict):
    title: str
    sections: List[Dict[str, str]]
    expanded_sections: List[Dict[str, str]]  # Added expanded sections

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
            
            # Create expanded sections
            expanded_sections = self.create_expanded_sections(sections)
            
            songs.append({
                'title': title,
                'sections': sections,
                'expanded_sections': expanded_sections
            })
        
        return songs
    
    def create_expanded_sections(self, sections: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Create expanded sections by repeating choruses after verses."""
        expanded = []
        active_chorus = None
        
        # First pass: add verses and choruses
        for i, section in enumerate(sections):
            if section['type'] == 'verse':
                # Add the verse
                expanded.append(section.copy())
                # Add the active chorus after the verse if:
                # 1. We have an active chorus
                # 2. We've seen a chorus before
                # 3. The next section is not a chorus
                if (active_chorus is not None and 
                    any(s['type'] == 'chorus' for s in sections[:i]) and
                    (i == len(sections) - 1 or sections[i + 1]['type'] != 'chorus')):
                    expanded.append(active_chorus.copy())
            elif section['type'] == 'chorus':
                active_chorus = section.copy()
                # Always add the chorus when we first encounter it
                expanded.append(section.copy())
        
        # Add the final active chorus after the last verse if needed
        if expanded and expanded[-1]['type'] == 'verse' and active_chorus is not None:
            expanded.append(active_chorus.copy())
        
        return expanded
    
    def clean_section_content(self, content: str, remove_verse_number: bool = False) -> str:
        """Clean section content by removing labels and extra whitespace."""
        lines = content.split('\n')
        
        # Remove verse number if needed
        if remove_verse_number and lines and any(lines[0].strip().startswith(f"{i}.") for i in range(1, 10)):
            lines[0] = lines[0].split('.', 1)[1].strip()
        
        # Remove chorus label if present
        if lines and any(label in lines[0].lower() for label in ['chorus', 'verse']):
            lines = lines[1:]
        
        return '\n'.join(line.strip() for line in lines if line.strip())

    def parse_lyrics(self, lyrics: str) -> List[Dict[str, str]]:
        """Parse lyrics into a list of stanzas and identify chorus."""
        # Split lyrics into stanzas
        stanzas = [s for s in lyrics.split('\n\n') if s.strip()]
        parsed_lyrics = []
        chorus_dict = {}  # Store choruses by their number/identifier
        verse_count = 0
        
        for stanza in stanzas:
            # Split into lines and remove empty lines
            lines = [line for line in stanza.split('\n') if line.strip()]
            if not lines:
                continue
            
            # Get the first non-empty line for analysis
            first_non_empty = lines[0].strip()
            
            # Check if this is a standalone chorus reference (e.g., "Chorus 1")
            if len(lines) == 1 and first_non_empty.lower().startswith('chorus '):
                chorus_num = first_non_empty.split(' ')[-1].strip(':')
                if chorus_num in chorus_dict:
                    # This is a reference to an existing chorus
                    parsed_lyrics.append(chorus_dict[chorus_num].copy())
                continue
            
            # Check if this is a labeled chorus (e.g., "Chorus 1:")
            if first_non_empty.lower().startswith('chorus '):
                chorus_num = first_non_empty.split(' ')[-1].strip(':')
                content = self.clean_section_content(stanza)
                
                section = {
                    'type': 'chorus',
                    'content': content,
                    'number': int(chorus_num)
                }
                
                chorus_dict[chorus_num] = section.copy()
                parsed_lyrics.append(section)
                continue
            
            # Check if this is an indented chorus
            is_indented_chorus = any(line.startswith('        ') for line in lines)
            if is_indented_chorus:
                chorus_num = str(len(chorus_dict) + 1)
                content = self.clean_section_content(stanza)
                
                section = {
                    'type': 'chorus',
                    'content': content,
                    'number': int(chorus_num)
                }
                
                chorus_dict[chorus_num] = section.copy()
                parsed_lyrics.append(section)
                continue
            
            # This must be a verse
            verse_count += 1
            number = None
            
            # Check for verse number at the start
            if lines[0].strip().startswith(tuple(f"{i}." for i in range(1, 10))):
                number = int(lines[0][0])
            else:
                number = verse_count
            
            # Clean up the content, removing verse number
            content = self.clean_section_content(stanza, remove_verse_number=True)
            
            # Create the section
            section = {
                'type': 'verse',
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
        print("\nOriginal sections:")
        for section in song['sections']:
            section_type = section['type']
            number = f" {section['number']}" if section['number'] is not None else ""
            print(f"\n{section_type.capitalize()}{number}:")
            print(section['content'])
            
        print("\nExpanded sections:")
        for section in song['expanded_sections']:
            section_type = section['type']
            number = f" {section['number']}" if section['number'] is not None else ""
            print(f"\n{section_type.capitalize()}{number}:")
            print(section['content'])

if __name__ == '__main__':
    main() 