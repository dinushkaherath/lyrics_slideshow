# config.py
from typing import Dict, Any
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def configure_defaults() -> Dict[str, Any]:
    """
    Presents a menu to edit default settings and returns a complete
    config dictionary.
    """

    # --- Default Dictionaries ---
    FONT = {
        "title": "Grathik",
        "body": "Grathik",
        "header": "Grathik",
    }

    SIZE = {
        "title": 44,
        "header": 24,
        "stanza": 44,
        "chorus": 44,
        "song_list": 14,
    }

    COLOR = {
        "bg": "2D1412",
        "header_bg": "BE4736",
        "text": "FFFFFF",
        "header_text": "FFFFFF",
    }

    HEADER_BG = {"enabled": "y"}

    OPTIONS = {
        1: ("Fonts", FONT),
        2: ("Font Sizes", SIZE),
        3: ("Colors", COLOR),
        4: ("Header Background Strip", HEADER_BG),
    }

    def print_options():
        print("\n=== Configuration Menu ===")
        for num, (label, values) in OPTIONS.items():
            print(f"\n[{num}] {label}:")
            for k, v in values.items():
                print(f"   {k}: {v}")
        print("\nPress ENTER to confirm and continue.\n")

    # --- Interactive Loop --- #
    while True:
        print_options()
        choice = input("Enter the number of the section to edit (or ENTER to finish): ").strip()

        if not choice:
            break

        if not choice.isdigit() or int(choice) not in OPTIONS:
            print("Invalid choice. Please try again.")
            continue

        section_name, section_dict = OPTIONS[int(choice)]
        print(f"\nEditing {section_name}:")

        for key, value in section_dict.items():
            new_val = input(f"  {key} [{value}]: ").strip()
            if new_val:
                # Handle numeric conversion for SIZE
                if section_name == "Font Sizes":
                    try:
                        section_dict[key] = int(new_val)
                    except ValueError:
                        print(f"  Invalid number '{new_val}', keeping original.")
                else:
                    section_dict[key] = new_val

    # --- Static Layout Dictionaries ---
    POSITION = {
        # Slide dimensions
        "slide_width": Inches(13.333),
        "slide_height": Inches(7.5),

        # Margins
        "left_margin": Inches(0.3),
        "right_margin": Inches(9.7),
        "bottom_margin": Inches(7),

        # Lyrics text box
        "lyrics_top": Inches(0),
        "lyrics_height": Inches(5),
        "lyrics_width": Inches(12.7),

        # Header
        "header_height": Inches(0.4),
        "header_width_left": Inches(10.7),
        "header_width_right": Inches(3),
        "header_left": Inches(9.5),
        "header_top": Inches(7),
        "title_top": Inches(3),
        "title_height": Inches(2),
    }

    ICON_SIZES = {
        "home": (Inches(0.4), Inches(0.4)),
        "restart": (Inches(0.93), Inches(0.75)),
    }

    ICON_POSITIONS = {
        "home": (
            POSITION["slide_width"] - ICON_SIZES["home"][0] - Inches(0.2),
            POSITION["bottom_margin"]
        ),
        "restart": (Inches(12.06), Inches(6)),
    }

    GRID = {
        "columns": 3,
        "box_width": Inches(4.45),
        "box_height": Inches(0.5),
        "spacing_x": Inches(0),
        "spacing_y": Inches(0),
        "start_left": Inches(0),
        "start_top": Inches(0),
    }

    # --- Assemble Final Config Dictionary ---
    config = {
        # Convert values on the fly
        "FONT": FONT,
        "SIZE": {k: Pt(v) for k, v in SIZE.items()},
        "COLOR": {k: RGBColor.from_string(v) for k, v in COLOR.items()},
        "backheadfil": HEADER_BG["enabled"].lower(),
        
        # Add static layouts
        "POSITION": POSITION,
        "ICON_SIZES": ICON_SIZES,
        "ICON_POSITIONS": ICON_POSITIONS,
        "GRID": GRID
    }
    
    return config