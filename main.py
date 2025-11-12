import os
import platform
import sys
import traceback

# 1. Import from our refactored files
from config import configure_defaults
from slideshow import LyricsSlideshow

# 2. Import your song parsing functions
try:
    from search_songs import match_and_compile_songs
    from alpha_order_songs import alpha_order
except ImportError:
    print("ERROR: Could not find 'search_songs.py' or 'alpha_order_songs.py'.")
    print("Please make sure those files are in the same directory as main.py.")
    sys.exit(1)


def main():
    try:
        # 1. Run your song parsing logic
        print("Starting song processing pipeline...")
        
        # This single line replaces search_songs, resolve_fuzzy_matches_and_merge, and compile_lyrics_tuples
        match_results, cleaned_tuples = match_and_compile_songs(
            "songs.json", 
            "target_songs.txt"
        )

        if not cleaned_tuples:
            print("No songs found or processed. Exiting.")
            return

        # Find all songs where there are no section (t[2] is num_choruses)
        zero_tuples = [t for t in cleaned_tuples if t[2] == 0]
        

        if zero_tuples:
            print("Songs that need help:")
            for t in zero_tuples:
                print(t[0], t[1], t[2])
            return

        song_list = [(num, name) for num, name, *_ in cleaned_tuples]
        print("Alphabetizing song list...")
        alpha_ordered_songs = alpha_order(song_list)

        # 2. Get configuration settings
        config = configure_defaults()

        # 3. Initialize the slideshow WITH the config
        print("Initializing slideshow...")
        slideshow = LyricsSlideshow(config)

        # 4. Generate the presentation
        output_file = "lyrics_slideshow.pptx"
        print(f"Generating presentation from {len(cleaned_tuples)} songs...")
        path = slideshow.create_presentation_from_parsed_sections(
            cleaned_tuples, 
            alpha_ordered_songs,
            output_file
        )

        # 5. Open the file (your auto-open logic)
        full_path = os.path.abspath(path)
        print(f"✅ PowerPoint created: {full_path}")

        if platform.system() == "Windows":
            os.startfile(full_path) # type: ignore
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open \"{full_path}\"")
        elif platform.system() == "Linux":
            try:
                # Most standard Linux desktop command
                os.system(f"xdg-open \"{full_path}\"")
            except Exception:
                # Fallback for WSL
                os.system(f"wslview \"{full_path}\"")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()