# Lyrics to Slides Converter

A Python application that converts song lyrics from a library into PowerPoint presentations, with intelligent song matching, lyrics parsing, and professional slide formatting.

## Overview

This tool matches songs from a target list against a comprehensive song library (JSON format), parses their lyrics into structured sections (verses/choruses), and generates a fully navigable PowerPoint presentation with clickable song indexes and professional formatting.

## Prerequisites

- Python 3.7 or higher
- Required Python packages (install via requirements.txt):
  - `python-pptx` - PowerPoint file generation
  - Additional dependencies for lyrics parsing and fuzzy matching

## Installation

Install all required packages:
```bash
pip install -r requirements.txt
```

## Project Structure

```
lyrics-slideshow/
├── main.py                    # Main entry point and orchestration
├── search_songs.py            # Song matching and compilation pipeline
├── slideshow.py               # PowerPoint presentation generation
├── utils.py                   # Helper functions (font sizing, text wrapping)
├── config.py                  # Configuration settings (fonts, colors, layout)
├── lyrics_parser.py           # Lyrics parsing and section detection
├── alpha_order_songs.py       # Alphabetical song ordering
├── songs.json                 # Song library database
├── target_songs.txt           # List of songs to include in presentation
├── selected_songs.json        # Cache of manual song selections
└── assets/
    ├── home.png              # Navigation icon
    └── restart.png           # Restart icon
```

## Usage

### 1. Update the Song Library (Optional)

To refresh your `songs.json` file with the latest from your song database:

```bash
python songbase-songs-json-updater.py
```

### 2. Create Your Target Song List

Create a file named `target_songs.txt` with your desired songs. The tool supports multiple input formats:

**Supported Formats:**
- Hymn number only: `512`
- Hymn number with title: `512 God is Good`
- Title with hymn reference: `God is Good (Hymn 512)`
- Title only: `Amazing Grace`

**Example `target_songs.txt`:**
```
512
Amazing Grace (Hymn 123)
10000 Reasons
Come Thou Fount of Every Blessing
```

### 3. Generate the Presentation

Run the main script:

```bash
python main.py
```

### 4. Interactive Song Matching

The script will:
1. **Match songs automatically** by hymn number or exact title
2. **Prompt for manual selection** when multiple matches are found
3. **Cache your choices** in `selected_songs.json` for future runs
4. **Generate the PowerPoint** file `lyrics_slideshow.pptx`
5. **Auto-open** the presentation (Windows/macOS/Linux)

## How It Works

### Song Matching Pipeline (`search_songs.py`)

1. **Match by Hymn Number**: Direct match using song database IDs
2. **Match by Title/Lyrics**: Exact substring matching in title or first line
3. **Fuzzy Matching**: Uses similarity algorithms (80%+ threshold) for partial matches
4. **Manual Resolution**: Interactive prompts for ambiguous matches
5. **Caching**: Saves manual selections to avoid re-prompting

### Lyrics Processing (`lyrics_parser.py`)

- Detects verses (numbered sections like "1.", "2.")
- Identifies choruses (indented or unlabeled sections)
- Handles multiple chorus variations
- Auto-repeats single choruses after each verse
- Splits long sections across multiple slides (9 lines max per slide)

### Presentation Generation (`slideshow.py`)

**Slide Types:**
1. **Title Slide**: Opening slide with presentation name
2. **Song List Index**: Grid of clickable song titles (numbered order)
3. **Alphabetical Index**: Grid of songs sorted A-Z with original numbers
4. **Lyric Slides**: Individual slides for each verse/chorus section

**Slide Features:**
- Headers showing song number, title, and section type
- Dynamic font sizing based on content length
- Italic formatting for chorus sections
- Navigation icons (home returns to index, restart goes to first slide of song)
- Clickable song titles in index grids
- Professional color schemes and typography

### Configuration (`config.py`)

Customize presentation appearance through configuration options:
- Fonts (title, header, body)
- Colors (background, text, header)
- Slide dimensions and margins
- Grid layout for song indexes
- Icon positions and sizes

## Features

✅ **Intelligent Song Matching**: Handles hymn numbers, titles, fuzzy matches, and interactive resolution  
✅ **Structured Lyrics Parsing**: Automatically detects verses and choruses  
✅ **Professional Formatting**: Consistent typography, dynamic font sizing, section styling  
✅ **Full Navigation**: Clickable indexes, home/restart icons, linked song titles  
✅ **Offline Operation**: Works completely offline once song library is loaded  
✅ **Customizable Design**: Fonts, colors, and layout via configuration  
✅ **Cross-Platform**: Supports Windows, macOS, and Linux  
✅ **Smart Caching**: Remembers manual song selections  
✅ **Auto-Splitting**: Long sections automatically split across multiple slides  

## Customization

### Changing Fonts

Edit `config.py` or respond to interactive prompts when running the script to customize:
- Title font
- Header font  
- Body text font

### Modifying Colors

Update the `COLOR` section in `config.py`:
```python
"COLOR": {
    "bg": RGBColor(255, 255, 255),      # Background color
    "text": RGBColor(0, 0, 0),          # Text color
    "header_bg": RGBColor(200, 200, 200), # Header background
    "header_text": RGBColor(0, 0, 0)    # Header text color
}
```

### Adjusting Layout

Modify positioning and sizing parameters in `config.py`:
- Margins and spacing
- Text box dimensions
- Grid layout for indexes
- Icon positions

## Troubleshooting

**"Songs that need help" message**  
Some songs have no detectable sections (verses/chorus). Check the song lyrics format in `songs.json`.

**Fuzzy match prompts keep appearing**  
The script caches your selections in `selected_songs.json`. Delete this file to reset all choices.

**Slides have text overflow**  
The dynamic font sizing should prevent this, but you can adjust `base_size` and `min_size` in `utils.py`.

**Icons not appearing**  
Ensure `assets/home.png` and `assets/restart.png` exist in your project directory.

## Output

The script generates:
- `lyrics_slideshow.pptx` - The final PowerPoint presentation
- `selected_songs.json` - Cache of your manual song selections

## Technical Details

**Lyrics Parsing Logic:**
- Verses identified by leading numbers (1., 2., etc.)
- Choruses identified by indentation or unlabeled sections
- Multiple chorus handling for complex songs
- Auto-repeat for songs with a single chorus

**PowerPoint Generation:**
- Uses `python-pptx` library
- Blank slide layout (fully customizable)
- Programmatic shape and text box creation
- Hyperlink actions for clickable navigation

**Font Sizing Algorithm:**
- Estimates visual line count based on character wrapping
- Scales font down from base size to fit content
- Maintains minimum readable size (18pt)
- Separate sizing for verses vs. choruses

## License

This project is for personal or organizational use. Ensure you have appropriate rights to the song lyrics in your library.

## Support

For issues or questions:
1. Check that all required files are present
2. Verify `songs.json` format matches expected structure
3. Review error messages for specific file or parsing issues
4. Ensure all dependencies are installed via `pip install -r requirements.txt`