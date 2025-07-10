import os
import platform
from lyrics_to_slides import LyricsSlideshow
from search_songs import compile_lyrics_tuples, search_songs

def main():
    result = search_songs("songs.json", "target_songs.txt")
    cleaned_tuples = compile_lyrics_tuples(result)

    slideshow = LyricsSlideshow()
    path = slideshow.create_presentation_from_parsed_sections(cleaned_tuples)

    full_path = os.path.abspath(path)
    print(f"✅ PowerPoint created: {full_path}")

    # Open the file automatically
    if platform.system() == "Windows":
        os.startfile(full_path)
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open \"{full_path}\"")
    elif platform.system() == "Linux":
        os.system(f"xdg-open \"{full_path}\"")

if __name__ == "__main__":
    main()
