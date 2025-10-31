import os
import json
from typing import List, Tuple, Optional

ORDER_FILE = "song_order.json"

# Type alias: list of (song_number, title)
SongList = List[Tuple[int, str]]


def generate_alphabetical_index(songs: SongList) -> SongList:
    """
    Return songs sorted alphabetically by title.
    """
    return sorted(songs, key=lambda x: x[1].lower())


def load_song_order() -> Optional[SongList]:
    """
    Load a previously saved song order as a list of (number, title) pairs.
    Returns None if no file exists.
    """
    if not os.path.exists(ORDER_FILE):
        return None
    with open(ORDER_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Validate and clean
    if not all(isinstance(i, list) and len(i) == 2 for i in data):
        print("⚠️ Invalid format in saved order, ignoring file.")
        return None
    return [(int(num), str(title)) for num, title in data]


def save_song_order(order: SongList) -> None:
    """
    Save the current song order (list of (number, title) pairs) to disk.
    """
    with open(ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(order, f, indent=2, ensure_ascii=False)
    print(f"✅ Song order saved to {ORDER_FILE}")


def interactive_reorder(songs: SongList) -> SongList:
    """
    Display songs alphabetically, allow the user to swap order, and save the final arrangement.
    Returns the reordered list of (number, title) tuples.
    """
    # Start alphabetically
    songs = generate_alphabetical_index(songs)
    print("\n🎶 Current alphabetical order:")
    for i, (num, title) in enumerate(songs, 1):
        print(f"  {i}. {num:02d} — {title}")

    while True:
        choice = input("\nEnter two numbers to swap (e.g. '3 5'), or 's' to save: ").strip()
        if choice.lower() == "s":
            save_song_order(songs)
            break
        try:
            a, b = map(int, choice.split())
            if 1 <= a <= len(songs) and 1 <= b <= len(songs):
                songs[a-1], songs[b-1] = songs[b-1], songs[a-1]
                print("\nUpdated order:")
                for i, (num, title) in enumerate(songs, 1):
                    print(f"  {i}. {num:02d} — {title}")
            else:
                print("⚠️ Invalid numbers, try again.")
        except ValueError:
            print("⚠️ Invalid input, enter two numbers or 's'.")

    return songs


def alpha_order(songs):
    """
    Load saved song order if available and apply it to the given list.
    Falls back to interactive reorder if no saved order exists.
    """
    saved_order = load_song_order()
    if saved_order:
        print("✅ Using saved song order from file.")
        # Map title to full tuple (handles full tuples with extra fields)
        title_to_song = {song[1]: song for song in songs}
        ordered = [title_to_song[t[1]] for t in saved_order if t[1] in title_to_song]
        return ordered

    print("⚠️ No saved order found — launching interactive reorder.")
    return interactive_reorder(songs)
