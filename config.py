# config.py
import json
import os
from typing import Dict, Any
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

CONFIG_SAVE_FILE = "config_settings.json"

def configure_defaults() -> Dict[str, Any]:
    """
    Presents a menu to edit settings, saves them to disk, and returns the config.
    """

    # --- 1. Define Default Dictionaries ---
    FONT = {"title": "Grathik", "body": "Grathik", "header": "Grathik"}
    SIZE = {"title": 44, "header": 24, "stanza": 44, "chorus": 44, "song_list": 14}
    COLOR = {"bg": "1E6B2C", "header_bg": "F2C037", "text": "FFFFFF", "header_text": "2D1412"}
    HEADER_BG = {"enabled": "y"}

    # --- 2. Load Saved Choices from Disk ---
    if os.path.exists(CONFIG_SAVE_FILE):
        try:
            with open(CONFIG_SAVE_FILE, "r") as f:
                saved_data = json.load(f)
                FONT.update(saved_data.get("FONT", {}))
                SIZE.update(saved_data.get("SIZE", {}))
                COLOR.update(saved_data.get("COLOR", {}))
                HEADER_BG.update(saved_data.get("HEADER_BG", {}))
            print(f"✅ Loaded saved configuration from {CONFIG_SAVE_FILE}")
        except Exception as e:
            print(f"⚠️ Could not load saved config: {e}")

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

    # --- 3. Interactive Loop ---
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

    # --- 4. Save Updated Choices to Disk ---
    try:
        with open(CONFIG_SAVE_FILE, "w") as f:
            json.dump({
                "FONT": FONT,
                "SIZE": SIZE,
                "COLOR": COLOR,
                "HEADER_BG": HEADER_BG
            }, f, indent=4)
        print(f"💾 Configuration saved to {CONFIG_SAVE_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to save configuration: {e}")

    # --- 5. Static Layout Dictionaries ---
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

    ICON_SIZES = {"home": (Inches(0.4), Inches(0.4)), "restart": (Inches(0.93), Inches(0.75))}
    ICON_POSITIONS = {
        "home": (POSITION["slide_width"] - ICON_SIZES["home"][0] - Inches(0.2), POSITION["bottom_margin"]),
        "restart": (Inches(12.06), Inches(6)),
    }
    GRID = {"columns": 3, "box_width": Inches(4.45), "box_height": Inches(0.5), "spacing_x": Inches(0), "spacing_y": Inches(0), "start_left": Inches(0), "start_top": Inches(0)}

    # --- 6. Assemble Final Config Dictionary ---
    return {
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
