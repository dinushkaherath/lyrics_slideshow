# Lyrics to Slides Converter

This Python script converts song lyrics into a PowerPoint presentation, with each verse and chorus on separate slides.
You can also grab all the songbase songs and put them into a file called songs.json

## Prerequisites

1. Python 3.7 or higher
2. python-pptx package

## Setup

1. Install the required package:
```bash
pip install -r requirements.txt
```

## Usage
0. If you would like for any reason to update the songbase `songs.json` file just run the `songbase-songs.json-updater.py` file.
```bash
python songbase-songs.json-updater.py
```

1. Create a text file named `target_songs.txt` with your target songs. It will then pull the songs from the `songs.json` file.
  
2. If you want to use other songs change/make a file called `songs.json`. Format requirements:
   - Number verses with "1.", "2.", etc. at the start
   - Indent chorus lines with spaces or tabs
   - Separate verses and chorus with blank lines

3. Run the script:
```bash
python create_slideshow.py
```

4. The script will create a PowerPoint file named `lyrics_slideshow.pptx` in the current directory.

Want to make it have different font?
  Answer the questions when you run it!
  If you dont know, or want default just click enter
## Features

- Automatically detects verses and chorus based on formatting
- Creates a clean, readable presentation
- Maintains consistent formatting across slides
- Differentiates between verses and chorus with styling
- Works completely offline
- Creates standard PowerPoint files that can be edited in any presentation software
- Custom fonts

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
