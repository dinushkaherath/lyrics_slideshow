from typing import List, Tuple, Dict
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR

# === Constants === #
FONT = {
    "title": "Lora",
    "body": "Helvetica",
    "header": "Calibri",
}

SIZE = {
    "title": Pt(44),
    "header": Pt(24),
    "stanza": Pt(28),
    "chorus": Pt(28),
}

COLOR = {
    "bg": RGBColor(45, 20, 18),
    "header_bg": RGBColor(190, 71, 54),
    "text": RGBColor(244, 243, 237),
    "header_text": RGBColor(244, 243, 237),
}

POSITION = {
    "slide_width": Inches(13.333),
    "slide_height": Inches(7.5),
    "left_margin": Inches(0.3),
    "right_margin": Inches(9.7),
    "bottom_margin": Inches(7),
    "width": Inches(12.7),
    "header_height": Inches(0.4),
    "lyrics_top": Inches(0.8),
    "lyrics_height": Inches(5),
}


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
        self.prs.slide_width = POSITION["slide_width"]
        self.prs.slide_height = POSITION["slide_height"]
        self.blank_layout = self.prs.slide_layouts[6]

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
        bottom = POSITION["bottom_margin"]

        # Insert the image
        try:
            icon = slide.shapes.add_picture(icon_path, left, bottom, width=icon_width, height=icon_height)
            icon.click_action.target_slide = target_slide
        except Exception as e:
            print(f"Error adding home icon: {e}")

    def _add_restart_song_icon(self, slide, target_slide, icon_path="assets/restart.png"):
        """
        Adds a clickable 'restart song' icon in the top-right corner of the slide.
        Clicking it takes the user to the first slide of the song.

        Args:
            slide: The slide to add the icon to.
            target_slide: The slide to link to (first slide of the song).
            icon_path (str): Path to the restart icon image.
        """
        icon_width = Inches(0.93)
        icon_height = Inches(0.75)
        left = Inches(12.06)
        top = Inches(6)

        try:
            pic = slide.shapes.add_picture(icon_path, left, top, width=icon_width, height=icon_height)
            pic.click_action.target_slide = target_slide
        except Exception as e:
            print(f"⚠️ Error adding restart icon: {e}")

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
            POSITION["bottom_margin"],
            POSITION["slide_width"],
            POSITION["header_height"] + Inches(0.1)
        )
        fill = header_shape.fill
        fill.solid()
        fill.fore_color.rgb = COLOR["header_bg"]
        header_shape.line.fill.background()  # No border
        return header_shape  # Return the shape for testing

    def _add_text_box(self, slide, text: str, left: float, top: float, width: float, height: float,
                      font_size: int, alignment=PP_ALIGN.CENTER, font_type=FONT["body"],
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
        font.color.rgb = COLOR["header_text"] if is_header else COLOR["text"]
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
            font.color.rgb = COLOR["header_text"] if is_header else COLOR["text"]
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
        title_slide.background.fill.solid()
        title_slide.background.fill.fore_color.rgb = COLOR["bg"]

        # Add main title
        self._add_text_box(
            slide=title_slide,
            text="Song Lyrics Slideshow",
            left=POSITION["left_margin"],
            top=Inches(3),
            width=POSITION["width"],
            height=Inches(2),
            font_size=SIZE["title"],
            font_type=FONT["title"]
        )

        song_titles = [song[1] for song in songs]

        # ====== Pass 1: Create all song slides ======
        song_slide_map = {}  # song index → first slide of that song

        for index, (song_number, title, chorus_count, sections) in enumerate(songs):
            for slide_index, section in enumerate(sections):
                slide = self.prs.slides.add_slide(self.blank_layout)

                if slide_index == 0:
                    song_slide_map[index] = slide

                # Set background color
                slide.background.fill.solid()
                slide.background.fill.fore_color.rgb = COLOR["bg"]

                # Add header background
                self._add_header_background(slide)

                # Add song number and title (top left)
                self._add_text_box(
                    slide=slide,
                    text=f"{song_number}: {title}",
                    left=POSITION["left_margin"],
                    top=POSITION["bottom_margin"],
                    width=Inches(10.7),
                    height=POSITION["header_height"] - Inches(0.05),
                    font_size=SIZE["header"],
                    alignment=PP_ALIGN.LEFT,
                    is_header=True,
                    font_type=FONT["header"]
                )

                section_type = section["type"].upper()
                section_label = (
                    f"CHORUS {section['number']}" if section_type == "CHORUS" and chorus_count > 1
                    else "CHORUS" if section_type == "CHORUS"
                    else f"STANZA {section['number']}"
                )

                self._add_text_box(
                    slide=slide,
                    text=section_label,
                    left=Inches(10),
                    top=POSITION["bottom_margin"],
                    width=Inches(2.5),
                    height=POSITION["header_height"] - Inches(0.05),
                    font_size=SIZE["header"],
                    alignment=PP_ALIGN.RIGHT,
                    is_header=True,
                    font_type=FONT["header"]
                )

                self._add_home_icon(slide, None)

                # Add lyrics content
                self._add_text_box(
                    slide=slide,
                    text=section['content'],
                    left=POSITION["left_margin"],
                    top=POSITION["lyrics_top"],
                    width=POSITION["width"],
                    height=POSITION["lyrics_height"],
                    font_size=SIZE["stanza"] if section['type'] == 'stanza' else SIZE["chorus"],
                    is_chorus=(section['type'] == 'chorus')
                )

                # Add restart song icon on last slide of song
                if slide_index == len(sections) - 1:
                    self._add_restart_song_icon(slide, song_slide_map[index])

        # ====== Pass 2: Add song list slide ======
        song_list_slide = self._add_song_list_slide(song_titles, song_slide_map)

        # ====== Pass 3: Patch home icons to point to song list slide ======
        for slide in self.prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "click_action"):
                    if getattr(shape.click_action, "target_slide", None) is None:
                        shape.click_action.target_slide = song_list_slide

        # Save the presentation
        self.prs.save(output_file)
        return output_file

    def _add_song_list_slide(self, song_titles: List[str], song_slide_map: Dict[int, 'Slide']):
        slide = self.prs.slides.add_slide(self.blank_layout)

        # Set background color
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = COLOR["header_bg"]

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
            shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, box_width, box_height)
            # Set fill color
            shape.fill.solid()
            shape.fill.fore_color.rgb = COLOR["header_bg"]

            # Set border (white thin line)
            shape.line.color.rgb = COLOR["header_text"]
            shape.line.width = Pt(0.75)

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
            run.font.name = FONT["body"]
            run.font.color.rgb = COLOR["text"]

            # Make each box clickable, linking to the corresponding song's first slide
            try:
                shape.click_action.target_slide = song_slide_map[slide_index]
            except Exception as e:
                print(f"Error linking song list item '{full_title}' to slide: {e}")

        return slide
