import unittest
import os
from lyrics_to_slides import LyricsSlideshow
from song_parser import SongParser
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE

class TestLyricsSlideshow(unittest.TestCase):
    def setUp(self):
        self.parser = SongParser()
        self.slideshow = LyricsSlideshow()
        self.test_songs = """Song 1
1. Praise the Lord, God sent His Son,
Hallelujah!
And salvation's work was done,
Glory to God!
God Himself became a man,
So that we might live in Him.

        That's why I call on Him,
        I give my all to Him.

2. For us He was crucified, Hallelujah!
For the many, one Man died,
Glory to God!
One grain fell into the earth,
Many grains to bring to birth.

3. He arose in victory, Hallelujah!
From the grave, triumphantly,
Glory to God!
Now in resurrection He
As the Spirit lives in me.

4. Call on Him from deep within,
Hallelujah!
Just by calling, He comes in,
Glory to God!
Once you call upon His name,
Nevermore you'll be the same.

        We all must call on Him,
        We give our all to Him.

Song 2
1. Have you been to Jesus for the cleansing pow'r?
Are you washed in the blood of the Lamb?
Are you fully trusting in His grace this hour?
Are you washed in the blood of the Lamb?

        Are you washed in the blood,
        In the soul-cleansing blood of the Lamb?
        Are your garments spotless? Are they white as snow?
        Are you washed in the blood of the Lamb?

2. Are you walking daily by the Savior's side?
Are you washed in the blood of the Lamb?
Do you rest each moment in the Crucified?
Are you washed in the blood of the Lamb?

3. When the Bridegroom cometh will your robes be white!
Are you washed in the blood of the Lamb?
Will your soul be ready for His presence bright,
And be washed in the blood of the Lamb?

4. Lay aside the garments that are stained with sin,
And be washed in the blood of the Lamb;
There's a fountain flowing for the soul unclean,
O be washed in the blood of the Lamb.

Song 3
1. In a low dungeon, hope we had none;
Tried to believe, but faith didn't come.
God, our sky clearing, Jesus appearing,
We by God were transfused!
We by God were transfused!

        Propitiation made by the blood,
        Jesus' redemption bought us for God!
        No condemnation, justification!
        We have peace toward God!
        We have peace toward God!

2. Born into Adam, dying we were;
We had a sickness no one could cure.
God, His Son sending, old Adam ending;
He is dead; we are free!
He is dead; we are free!

3. Now we're rejoicing, standing in grace,
Oh, hallelujah! Sin is erased!
God in us flowing, in our hearts growing,
We are saved in His life!
We are saved in His life!"""
        
        self.test_output = "test_slideshow.pptx"
        
    def tearDown(self):
        # Clean up test file after each test
        if os.path.exists(self.test_output):
            os.remove(self.test_output)

    def test_presentation_creation(self):
        """Test that the presentation is created successfully."""
        songs = self.parser.parse_songs(self.test_songs)
        output_file = self.slideshow.create_presentation(songs, self.test_output)
        
        self.assertTrue(os.path.exists(output_file))
        
        # Load the presentation and check its structure
        prs = Presentation(output_file)
        
        # Calculate expected number of slides:
        # 1 (main title) + 
        # For each song:
        #   number of sections
        expected_slides = 1  # Main title
        for song in songs:
            expected_slides += len(song['sections'])  # One slide per section
            
        self.assertEqual(len(prs.slides), expected_slides)

    def test_slide_content_types(self):
        """Test that slides have the correct content types."""
        songs = self.parser.parse_songs(self.test_songs)
        output_file = self.slideshow.create_presentation(songs, self.test_output)
        
        prs = Presentation(output_file)
        
        # First slide should be main title
        first_slide = prs.slides[0]
        # Get all text from all shapes on the first slide
        title_text = ""
        for shape in first_slide.shapes:
            if hasattr(shape, "text_frame"):
                title_text = shape.text_frame.text.strip()
                if title_text:
                    break
        self.assertEqual(title_text, "Song Lyrics Slideshow")
        
        # Second slide should be first verse of first song
        second_slide = prs.slides[1]
        song_title = ""
        verse_header = ""
        for shape in second_slide.shapes:
            if hasattr(shape, "text_frame"):
                text = shape.text_frame.text.strip()
                if "SONG 1" in text:
                    song_title = text
                elif "STANZA" in text:
                    verse_header = text
        self.assertEqual(song_title, "SONG 1")
        self.assertEqual(verse_header, "STANZA 1")

    def test_slide_styling(self):
        """Test that slides have the correct styling."""
        songs = self.parser.parse_songs(self.test_songs)
        output_file = self.slideshow.create_presentation(songs, self.test_output)
        
        prs = Presentation(output_file)
        
        # Check content slide (second slide)
        content_slide = prs.slides[1]
        
        # Check main background color
        background = content_slide.background
        fill = background.fill
        self.assertTrue(fill.type)  # Should be solid fill
        self.assertEqual(fill.fore_color.rgb, self.slideshow.BACKGROUND_COLOR)
        
        # Check header background shape
        header_shape = None
        for shape in content_slide.shapes:
            if shape.shape_type == MSO_SHAPE.RECTANGLE:  # Rectangle shape for header background
                header_shape = shape
                break
        self.assertIsNotNone(header_shape, "Header background shape not found")
        self.assertEqual(header_shape.fill.fore_color.rgb, self.slideshow.HEADER_BACKGROUND_COLOR)
        
        # Check text formatting
        for shape in content_slide.shapes:
            if hasattr(shape, "text_frame"):
                text = shape.text_frame.text.strip()
                if text:  # Only check non-empty text boxes
                    if "SONG" in text or "STANZA" in text:
                        # Header text should be uppercase and have header color
                        self.assertTrue(text.isupper())
                        font = shape.text_frame.paragraphs[0].font
                        if font.color.type is not None:  # Only check if color is set
                            self.assertEqual(font.color.rgb, self.slideshow.HEADER_TEXT_COLOR)
                    else:
                        # Content text should have main text color
                        font = shape.text_frame.paragraphs[0].font
                        if font.color.type is not None:  # Only check if color is set
                            self.assertEqual(font.color.rgb, self.slideshow.TEXT_COLOR)

if __name__ == '__main__':
    unittest.main() 