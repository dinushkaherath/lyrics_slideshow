from typing import List, Tuple, Dict
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

class LyricsSlideshow:
    def __init__(self):
        """
        Creates PowerPoint presentations from parsed song lyrics with consistent formatting and styling.
        
        Features:
        - Creates slides with dark theme and professional typography
        - Maintains consistent layout across all slides
        - Differentiates verses and choruses through styling
        - Includes header information for song and section numbers
        
        Styling constants:
        - Fonts: Helvetica Neue for both titles and body text
        - Colors: Dark gray background with white text
        - Sizes: Different font sizes for titles, headers, verses, and choruses
        """
        self.prs = Presentation()
        self.blank_layout = self.prs.slide_layouts[6]  # Blank layout instead of Title Only layout
        
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
        
        # Define positions - Maximizing width by reducing margins
        self.LEFT_MARGIN = Inches(0.3)  # Reduced from 1
        self.RIGHT_MARGIN = Inches(9.7)  # Increased from 9
        self.TOP_MARGIN = Inches(0.05)  # Keep this the same for header
        self.WIDTH = Inches(9.4)  # Increased from 8 (difference between RIGHT_MARGIN and LEFT_MARGIN)
        self.HEADER_HEIGHT = Inches(0.4)  # Keep this the same
        self.LYRICS_TOP = Inches(0.8)  # Keep this the same
        self.LYRICS_HEIGHT = Inches(5)  # Keep this the same

    def _add_header_background(self, slide):
        """
        Adds a darker background strip for the header section of each slide.
        
        Creates a rectangular shape at the top of the slide that:
        - Spans the full width of the slide
        - Has a slightly darker color than the main background
        - Contains no border
        - Provides visual separation between header and content
        
        Args:
            slide: PowerPoint slide object to add the header background to
            
        Returns:
            The created shape object for testing purposes
        """
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
                      font_size: int, alignment=PP_ALIGN.CENTER, is_title=False,
                      is_chorus=False, is_header=False):
        """
        Creates a formatted text box on the slide with specified parameters.
        
        Formatting features:
        - Handles multi-line text with consistent spacing
        - Applies different styles for titles, headers, verses, and choruses
        - Supports text alignment and word wrap
        - Uses specified font sizes and colors
        - Applies italic formatting for chorus sections
        
        Args:
            slide: PowerPoint slide to add the text box to
            text (str): Content to display
            left (float): Left position of the text box
            top (float): Top position of the text box
            width (float): Width of the text box
            height (float): Height of the text box
            font_size (int): Size of the font in points
            alignment: Text alignment (default: center)
            is_title (bool): Whether this is a title text box
            is_chorus (bool): Whether this is a chorus section
            is_header (bool): Whether this is a header text box
            
        Returns:
            The created shape object
        """
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

    def create_presentation_from_parsed_sections(self, songs: List[Tuple[int, str, int, List[Dict]]], output_file: str = "lyrics_slideshow.pptx") -> str:
        """
        Creates a complete PowerPoint presentation from a list of parsed songs.
        
        Process:
        1. Creates a title slide with presentation name
        2. For each song:
        - Creates slides for each expanded section (verse/chorus)
        - Adds consistent headers with song and section numbers
        - Formats content according to section type
        3. Saves the presentation to specified file
        
        Slide Structure:
        - Dark background with lighter header strip
        - Song number and title in top left
        - Section type and number in top right
        - Main content in center with appropriate formatting
        
        Args:
            songs (List[Song]): List of parsed song dictionaries
            output_file (str): Desired output filename
            
        Returns:
            str: Path to the created presentation file
        """
        # Add title slide
        title_slide = self.prs.slides.add_slide(self.blank_layout)

        # Set background color for title slide
        background = title_slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = self.BACKGROUND_COLOR

        # Add main title
        self._add_text_box(
            title_slide,
            "Song Lyrics Slideshow",
            self.LEFT_MARGIN,
            Inches(3),
            self.WIDTH,
            Inches(2),
            self.TITLE_SIZE,
            is_title=True
        )

        for song_number, title, chorus_count, sections in songs:
            for section in sections:
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
                    f"{song_number}: {title}",
                    self.LEFT_MARGIN,
                    self.TOP_MARGIN,
                    Inches(6.5),
                    self.HEADER_HEIGHT - Inches(0.05),
                    self.HEADER_SIZE,
                    alignment=PP_ALIGN.LEFT,
                    is_header=True
                )

                section_type = section["type"].upper()
                section_label = f"{section_type} {section['number']}" if (section_type == "CHORUS" and chorus_count > 1) or section_type == "STANZA" else section_type

                self._add_text_box(
                    slide,
                    section_label,
                    Inches(7),
                    self.TOP_MARGIN,
                    Inches(2.5),
                    self.HEADER_HEIGHT - Inches(0.05),
                    self.HEADER_SIZE,
                    alignment=PP_ALIGN.RIGHT,
                    is_header=True
                )

                # Add lyrics content with maximum width
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
