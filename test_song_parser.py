import unittest
from song_parser import SongParser

class TestSongParser(unittest.TestCase):
    def setUp(self):
        self.parser = SongParser()
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

    def test_song_count(self):
        """Test that the parser correctly identifies three songs."""
        songs = self.parser.parse_songs(self.test_songs)
        self.assertEqual(len(songs), 3)

    def test_song_titles(self):
        """Test that song titles are correctly parsed."""
        songs = self.parser.parse_songs(self.test_songs)
        expected_titles = ["Song 1", "Song 2", "Song 3"]
        for song, expected_title in zip(songs, expected_titles):
            self.assertEqual(song['title'], expected_title)

    def test_song1_structure(self):
        """Test the structure of Song 1."""
        songs = self.parser.parse_songs(self.test_songs)
        song1 = songs[0]
        
        # Should have 6 sections: 4 verses and 2 choruses
        self.assertEqual(len(song1['sections']), 6)
        
        # Check verse numbers
        verses = [section for section in song1['sections'] if section['type'] == 'verse']
        verse_numbers = [verse['number'] for verse in verses]
        self.assertEqual(verse_numbers, [1, 2, 3, 4])
        
        # Check chorus count
        chorus_count = sum(1 for section in song1['sections'] if section['type'] == 'chorus')
        self.assertEqual(chorus_count, 2)

    def test_song2_structure(self):
        """Test the structure of Song 2."""
        songs = self.parser.parse_songs(self.test_songs)
        song2 = songs[1]
        
        # Should have 5 sections: 4 verses and 1 chorus
        self.assertEqual(len(song2['sections']), 5)
        
        # Check verse numbers
        verses = [section for section in song2['sections'] if section['type'] == 'verse']
        verse_numbers = [verse['number'] for verse in verses]
        self.assertEqual(verse_numbers, [1, 2, 3, 4])
        
        # Check chorus count
        chorus_count = sum(1 for section in song2['sections'] if section['type'] == 'chorus')
        self.assertEqual(chorus_count, 1)

    def test_song3_structure(self):
        """Test the structure of Song 3."""
        songs = self.parser.parse_songs(self.test_songs)
        song3 = songs[2]
        
        # Should have 4 sections: 3 verses and 1 chorus
        self.assertEqual(len(song3['sections']), 4)
        
        # Check verse numbers
        verses = [section for section in song3['sections'] if section['type'] == 'verse']
        verse_numbers = [verse['number'] for verse in verses]
        self.assertEqual(verse_numbers, [1, 2, 3])
        
        # Check chorus count
        chorus_count = sum(1 for section in song3['sections'] if section['type'] == 'chorus')
        self.assertEqual(chorus_count, 1)

    def test_chorus_content(self):
        """Test that chorus content is correctly parsed and stripped."""
        songs = self.parser.parse_songs(self.test_songs)
        choruses = [section for section in songs[0]['sections'] if section['type'] == 'chorus']
        self.assertTrue(len(choruses) > 0, "No chorus found in Song 1")
        
        first_chorus = choruses[0]
        expected_content = "That's why I call on Him,\nI give my all to Him."
        self.assertEqual(first_chorus['content'], expected_content)

    def test_verse_content(self):
        """Test that verse content is correctly parsed and stripped."""
        songs = self.parser.parse_songs(self.test_songs)
        verses = [section for section in songs[0]['sections'] if section['type'] == 'verse']
        self.assertTrue(len(verses) > 0, "No verses found in Song 1")
        
        first_verse = verses[0]
        expected_content = "Praise the Lord, God sent His Son,\nHallelujah!\nAnd salvation's work was done,\nGlory to God!\nGod Himself became a man,\nSo that we might live in Him."
        self.assertEqual(first_verse['content'], expected_content)

if __name__ == '__main__':
    unittest.main() 