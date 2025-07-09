import os
from lyrics_to_slides import LyricsSlideshow
from search_songs import get_cleaned_lyrics_tuples, search_songs, load_target_songs

song_titles = [d['original'] for d in load_target_songs('target_songs.txt')] # TODO move this into LyricsSlideshow

def main():
    result = search_songs("songs.json", "target_songs.txt")
    cleaned_tuples = get_cleaned_lyrics_tuples(result)

    slideshow = LyricsSlideshow()
    slideshow.add_song_list_slide(song_titles)
    path = slideshow.create_presentation_from_parsed_sections(cleaned_tuples)
    print(f"✅ PowerPoint created: {os.path.abspath(path)}")

if __name__ == "__main__":
    main()
