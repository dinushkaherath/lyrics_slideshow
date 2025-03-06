from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from typing import List, Dict
import os
from song_parser import SongParser, Song

class LyricsSlideshow:
    def __init__(self):
        self.prs = Presentation()
        self.blank_layout = self.prs.slide_layouts[5]  # Title Only layout
        
        # Define styles
        self.TITLE_FONT = "Helvetica Neue"
        self.BODY_FONT = "Helvetica Neue"
        self.TITLE_SIZE = Pt(44)  # Main title slide
        self.HEADER_SIZE = Pt(24)  # Top headers on content slides
        self.VERSE_SIZE = Pt(32)   # Reduced from 44
        self.CHORUS_SIZE = Pt(28)  # Reduced from 40
        
        # Define colors
        self.BACKGROUND_COLOR = RGBColor(40, 40, 40)  # Dark gray background
        self.HEADER_BACKGROUND_COLOR = RGBColor(30, 30, 30)  # Slightly darker for header
        self.TEXT_COLOR = RGBColor(255, 255, 255)  # White text
        self.HEADER_TEXT_COLOR = RGBColor(200, 200, 200)  # Slightly dimmed white for headers
        
        # Define positions
        self.LEFT_MARGIN = Inches(1)
        self.RIGHT_MARGIN = Inches(9)
        self.TOP_MARGIN = Inches(0.05)  # Reduced from 0.2 to move text closer to top
        self.WIDTH = Inches(8)
        self.HEADER_HEIGHT = Inches(0.4)  # Keep this the same
        self.LYRICS_TOP = Inches(0.8)  # Keep this the same
        self.LYRICS_HEIGHT = Inches(5)  # Keep this the same

    def _add_header_background(self, slide):
        """Add a darker background for the header area."""
        header_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            0,  # Left
            0,  # Top
            Inches(10),  # Width (full slide width)
            self.HEADER_HEIGHT + Inches(0.1)  # Height - slightly taller than text for padding
        )
        fill = header_shape.fill
        fill.solid()
        fill.fore_color.rgb = self.HEADER_BACKGROUND_COLOR
        header_shape.line.fill.background()  # No border
        return header_shape  # Return the shape for testing

    def _add_text_box(self, slide, text: str, left: float, top: float, width: float, height: float, 
                     font_size: int, alignment=PP_ALIGN.CENTER, is_title: bool = False, is_chorus: bool = False, is_header: bool = False):
        """Add a text box to the slide with specified formatting."""
        shape = slide.shapes.add_textbox(left, top, width, height)
        text_frame = shape.text_frame
        text_frame.word_wrap = True
        text_frame.auto_size = None  # Let text wrap within the box
        
        # Split text into lines and add each line as a separate paragraph
        lines = text.split('\n')
        
        # Add first line
        first_paragraph = text_frame.paragraphs[0]
        first_paragraph.text = lines[0].upper() if is_header else lines[0]
        first_paragraph.alignment = alignment
        first_paragraph.line_spacing = 1.0  # Single line spacing
        
        # Format first paragraph
        font = first_paragraph.font
        font.size = font_size
        font.name = self.TITLE_FONT if is_title else self.BODY_FONT
        font.color.rgb = self.HEADER_TEXT_COLOR if is_header else self.TEXT_COLOR
        if is_chorus:
            font.italic = True
            
        # Add remaining lines
        for line in lines[1:]:
            paragraph = text_frame.add_paragraph()
            paragraph.text = line.upper() if is_header else line
            paragraph.alignment = alignment
            paragraph.line_spacing = 1.0  # Single line spacing
            
            # Format paragraph
            font = paragraph.font
            font.size = font_size
            font.name = self.TITLE_FONT if is_title else self.BODY_FONT
            font.color.rgb = self.HEADER_TEXT_COLOR if is_header else self.TEXT_COLOR
            if is_chorus:
                font.italic = True
                
        return shape

    def create_presentation(self, songs: List[Song], output_file: str = "lyrics_slideshow.pptx") -> str:
        """Create a new presentation with multiple songs."""
        # Add title slide
        title_slide = self.prs.slides.add_slide(self.blank_layout)
        
        # Set background color for title slide
        background = title_slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self.BACKGROUND_COLOR
        
        # Add main title
        title_shape = self._add_text_box(
            title_slide, 
            "Song Lyrics Slideshow",
            self.LEFT_MARGIN,
            Inches(3),
            self.WIDTH,
            Inches(2),
            self.TITLE_SIZE,
            is_title=True
        )

        # Process each song
        for song_index, song in enumerate(songs, 1):
            # Add slides for each section
            for section in song['sections']:
                slide = self.prs.slides.add_slide(self.blank_layout)
                
                # Set background color
                background = slide.background
                fill = background.fill
                fill.solid()
                fill.fore_color.rgb = self.BACKGROUND_COLOR
                
                # Add header background
                self._add_header_background(slide)
                
                # Add song number and title (top left)
                self._add_text_box(
                    slide,
                    f"SONG {song_index}",
                    self.LEFT_MARGIN,
                    self.TOP_MARGIN,
                    Inches(6),
                    self.HEADER_HEIGHT - Inches(0.05),  # Slightly reduce height to prevent overflow
                    self.HEADER_SIZE,
                    alignment=PP_ALIGN.LEFT,
                    is_header=True
                )
                
                # Add section number (top right)
                section_title = f"CHORUS {section['number']}" if section['type'] == 'chorus' else f"STANZA {section['number']}"
                self._add_text_box(
                    slide,
                    section_title,
                    Inches(7),
                    self.TOP_MARGIN,
                    Inches(2),
                    self.HEADER_HEIGHT - Inches(0.05),  # Slightly reduce height to prevent overflow
                    self.HEADER_SIZE,
                    alignment=PP_ALIGN.RIGHT,
                    is_header=True
                )
                
                # Add lyrics content
                self._add_text_box(
                    slide,
                    section['content'],
                    self.LEFT_MARGIN,
                    self.LYRICS_TOP,
                    self.WIDTH,
                    self.LYRICS_HEIGHT,
                    self.VERSE_SIZE if section['type'] == 'verse' else self.CHORUS_SIZE,
                    is_chorus=(section['type'] == 'chorus')
                )

        # Save the presentation
        self.prs.save(output_file)
        return output_file

def main():
    # Example usage
    parser = SongParser()
    slideshow = LyricsSlideshow()
    
    # Get lyrics from a file
    with open('songs.txt', 'r') as f:
        songs_text = f.read()
    
    # Parse songs and create presentation
    songs = parser.parse_songs(songs_text)
    output_file = slideshow.create_presentation(songs)
    
    # Get absolute path
    abs_path = os.path.abspath(output_file)
    print(f"Created presentation: {abs_path}")

if __name__ == '__main__':
    main() 