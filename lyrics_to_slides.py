from typing import List, Tuple, Dict
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR


class LyricsSlideshow:
    def __init__(self):
        """
        Creates PowerPoint presentations from parsed song lyrics with consistent formatting and styling.
        
        Features:
        - Creates slides with dark theme and professional typography
        - Maintains consistent layout across all slides
        - Differentiates stanzas and choruses through styling
        - Includes header information for song and section numbers
        
        Styling constants:
        - Fonts: Helvetica Neue for both titles and body text
        - Colors: Dark gray background with white text
        - Sizes: Different font sizes for titles, headers, stanzas, and choruses
        """
        self.prs = Presentation()

        # Set slide size to 16:9
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)

        self.blank_layout = self.prs.slide_layouts[6]  # Blank layout instead of Title Only layout

        # Define styles
        self.TITLE_FONT = "Lora"
        self.BODY_FONT = "Helvetica"
        self.HEADER_FONT = "Calibri"
        self.TITLE_SIZE = Pt(44)  # Main title slide
        self.HEADER_SIZE = Pt(24)  # Top headers on content slides
        self.STANZA_SIZE = Pt(28)
        self.CHORUS_SIZE = Pt(28)

        # Define colors
        self.BACKGROUND_COLOR = RGBColor(45, 20, 18)
        self.HEADER_BACKGROUND_COLOR = RGBColor(190, 71, 54)
        self.TEXT_COLOR = RGBColor(244, 243, 237)
        self.HEADER_TEXT_COLOR = RGBColor(244, 243, 237)

        # Define positions - Maximizing width by reducing margins
        self.LEFT_MARGIN = Inches(0.3)  # Reduced from 1
        self.RIGHT_MARGIN = Inches(9.7)  # Increased from 9
        self.TOP_MARGIN = Inches(0.05)  # Keep this the same for header
        self.WIDTH = Inches(12.7)  # Increased from 8 (difference between RIGHT_MARGIN and LEFT_MARGIN)
        self.HEADER_HEIGHT = Inches(0.4)  # Keep this the same
        self.LYRICS_TOP = Inches(0.8)  # Keep this the same
        self.LYRICS_HEIGHT = Inches(5)  # Keep this the same

    def _calculate_dynamic_font_size(self, text: str, is_chorus: bool = False) -> Pt:
        """
        Dynamically calculates font size based on actual text wrapping.
        Assumes average character width and screen line width.
        """
        base_size = 28
        min_size = 18
        max_display_lines = 12 if is_chorus else 14
        max_chars_per_line = 50  # empirically reasonable for ~28pt on widescreen slide

        # Count actual visual lines based on wrap
        raw_lines = text.split('\n')
        estimated_line_count = sum((len(line) // max_chars_per_line + 1) for line in raw_lines)

        scale = min(1.0, max_display_lines / max(estimated_line_count, 1))
        size = int(base_size * scale)
        return Pt(max(size, min_size))

    def _add_home_icon(self, slide, target_slide, icon_path="assets/home.png"):
        """
        Adds a clickable home PNG icon in the top-right corner that links to the target_slide.

        Args:
            slide: The slide to add the icon to.
            target_slide: The slide to link back to (song list).
            icon_path: Path to the PNG file to use as the icon.
        """
        icon_width = Inches(0.4)
        icon_height = Inches(0.4)

        # Position at the far right, with a small margin
        left = self.prs.slide_width - icon_width - Inches(0.2)
        top = Inches(0.05)

        # Insert the image
        try:
            icon = slide.shapes.add_picture(icon_path, left, top, width=icon_width, height=icon_height)
            icon.click_action.target_slide = target_slide
        except Exception as e:
            print(f"Error adding home icon: {e}")


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
            Inches(13.333),  # Width (full slide width)
            self.HEADER_HEIGHT + Inches(0.1)  # Height - slightly taller than text for padding
        )
        fill = header_shape.fill
        fill.solid()
        fill.fore_color.rgb = self.HEADER_BACKGROUND_COLOR
        header_shape.line.fill.background()  # No border
        return header_shape  # Return the shape for testing

    def _add_text_box(self, slide, text: str, left: float, top: float, width: float, height: float,
                      font_size: int, alignment=PP_ALIGN.CENTER, font_type="Helvetica",
                      is_chorus=False, is_header=False):
        """
        Creates a formatted text box on the slide with specified parameters.
        
        Formatting features:
        - Handles multi-line text with consistent spacing
        - Applies different styles for titles, headers, stanzas, and choruses
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
        text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE

        # Split text into lines and add each line as a separate paragraph
        lines = text.split('\n')

        if not is_header:
            font_size = self._calculate_dynamic_font_size(text, is_chorus)

        # Add first line
        first_paragraph = text_frame.paragraphs[0]
        first_paragraph.text = lines[0].upper() if is_header else lines[0]
        first_paragraph.alignment = alignment
        first_paragraph.line_spacing = 1.0  # Single line spacing

        # Format first paragraph
        font = first_paragraph.font
        font.size = font_size

        font.name = font_type
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
            font.name = font_type
            font.color.rgb = self.HEADER_TEXT_COLOR if is_header else self.TEXT_COLOR
            if is_chorus:
                font.italic = True

        return shape

    def create_presentation_from_parsed_sections(self,
                                                 songs: List[Tuple[int, str, int, List[Dict]]],
                                                 output_file: str = "lyrics_slideshow.pptx") -> str:
        """
        Creates a complete PowerPoint presentation from a list of parsed songs.
        
        Process:
        1. Creates a title slide with presentation name
        2. For each song:
        - Creates slides for each expanded section (stanza/chorus)
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
            font_type=self.TITLE_FONT
        )

        song_titles = [song[1] for song in songs]
        song_list_slide = self._add_song_list_slide(song_titles)

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
                    is_header=True,
                    font_type=self.HEADER_FONT
                )

                section_type = section["type"].upper()
                section_label = (
                    f"CHORUS {section['number']}" if section_type == "CHORUS" and chorus_count > 1
                    else "CHORUS" if section_type == "CHORUS"
                    else f"STANZA {section['number']}"
                )

                self._add_text_box(
                    slide,
                    section_label,
                    Inches(10),
                    self.TOP_MARGIN,
                    Inches(2.5),
                    self.HEADER_HEIGHT - Inches(0.05),
                    self.HEADER_SIZE,
                    alignment=PP_ALIGN.RIGHT,
                    is_header=True,
                    font_type=self.HEADER_FONT
                )

                self._add_home_icon(slide, song_list_slide)

                # Add lyrics content with maximum width
                self._add_text_box(
                    slide,
                    section['content'],
                    self.LEFT_MARGIN,
                    self.LYRICS_TOP,
                    self.WIDTH,
                    self.LYRICS_HEIGHT,
                    self.STANZA_SIZE if section['type'] == 'stanza' else self.CHORUS_SIZE,
                    is_chorus=(section['type'] == 'chorus')
                )

        # Save the presentation
        self.prs.save(output_file)
        return output_file

    def _add_song_list_slide(self, song_titles: List[str]):
        """
        Adds a clean grid-style slide listing all song titles, each inside a
        bordered rectangle with small font and no extra text boxes.
        Matches the provided visual style precisely.
        """
        slide = self.prs.slides.add_slide(self.blank_layout)

        # Set background color
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = self.HEADER_BACKGROUND_COLOR

        # Grid configuration
        num_columns = 3
        box_width = Inches(4.45)
        box_height = Inches(0.5)  # Smaller box
        spacing_x = Inches(0)
        spacing_y = Inches(0)
        left_start = Inches(0)
        top_start = Inches(0)

        for slide_index, title in enumerate(song_titles):
            col = slide_index % num_columns
            row = slide_index // num_columns
            number = slide_index + 1
            full_title = f"{number} – {title}"

            left = left_start + col * (box_width + spacing_x)
            top = top_start + row * (box_height + spacing_y)

            # Create the rectangle (serves as background + border + text container)
            shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                left,
                top,
                box_width,
                box_height
            )

            # Set fill color
            shape.fill.solid()
            shape.fill.fore_color.rgb = self.HEADER_BACKGROUND_COLOR

            # Set border (white thin line)
            shape.line.color.rgb = self.HEADER_TEXT_COLOR
            shape.line.width = Pt(0.75)

            # shape.click_action.target_slide = target_slide

            # Add text directly in shape
            text_frame = shape.text_frame
            text_frame.text = full_title
            text_frame.vertical_anchor = MSO_VERTICAL_ANCHOR.MIDDLE
            text_frame.word_wrap = True

            # Format paragraph
            p = text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT
            run = p.runs[0]
            run.font.size = Pt(14)  # Smaller font
            run.font.name = self.BODY_FONT
            run.font.color.rgb = self.TEXT_COLOR

        return slide
