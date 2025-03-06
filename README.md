# Lyrics to Slides Converter

This Python script converts song lyrics into a PowerPoint presentation, with each verse and chorus on separate slides.

## Prerequisites

1. Python 3.7 or higher
2. python-pptx package

## Setup

1. Install the required package:
```bash
pip install -r requirements.txt
```

## Usage

1. Create a text file named `lyrics.txt` with your song lyrics. Format requirements:
   - Number verses with "1.", "2.", etc. at the start
   - Indent chorus lines with spaces or tabs
   - Separate verses and chorus with blank lines

2. Run the script:
```bash
python lyrics_to_slides.py
```

3. The script will create a PowerPoint file named `lyrics_slideshow.pptx` in the current directory.

## Features

- Automatically detects verses and chorus based on formatting
- Creates a clean, readable presentation
- Maintains consistent formatting across slides
- Differentiates between verses and chorus with styling
- Works completely offline
- Creates standard PowerPoint files that can be edited in any presentation software

## Example Lyrics Format

```
1. First verse line
Second line
Third line

        Chorus line 1
        Chorus line 2
        Chorus line 3

2. Second verse line
Second line
Third line
``` 