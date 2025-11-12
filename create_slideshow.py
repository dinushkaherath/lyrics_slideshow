import os
import platform
from lyrics_to_slides import LyricsSlideshow
from search_songs import compile_lyrics_tuples, resolve_fuzzy_matches_and_merge, search_songs
from alpha_order_songs import alpha_order

def main():
    result = search_songs("songs.json", "target_songs.txt")
    result = resolve_fuzzy_matches_and_merge(result)
    cleaned_tuples = compile_lyrics_tuples(result)
    song_list = [(num, name) for num, name, *_ in cleaned_tuples]

    alpha_ordered_songs = alpha_order(song_list)

    slideshow = LyricsSlideshow()
    path = slideshow.create_presentation_from_parsed_sections(cleaned_tuples, alpha_ordered_songs)

    full_path = os.path.abspath(path)
    print(f"✅ PowerPoint created: {full_path}")

    # Open the file automatically
    if platform.system() == "Windows":
        os.startfile(full_path) # type: ignore
    elif platform.system() == "Darwin":  # macOS
        os.system(f"open \"{full_path}\"")
    elif platform.system() == "Linux":
        os.system(f"wslview \"{full_path}\"")

if __name__ == "__main__":
    main()
