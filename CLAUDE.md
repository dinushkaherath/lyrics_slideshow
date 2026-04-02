# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Program

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Run the full pipeline (generates lyrics_slideshow.pptx)
python main.py

# Run tests (note: test file references old module names and may not pass)
python -m unittest test_lyrics_slideshow.py
```

## Required Input Files

- `songs.json` — the song library (JSON with `songs` array and `books` array for hymn number mapping)
- `target_songs.txt` — list of songs to include, one per line

`target_songs.txt` supports multiple formats:
- `1232` — hymn number only
- `1232 Amazing Grace` — hymn number + title
- `Amazing Grace (Hymn 12)` — title + parenthetical hymn number
- `Amazing Grace 1232` — title + trailing number
- `Amazing Grace` — title only (fuzzy matched)

## Pipeline Architecture

`main.py` orchestrates three sequential stages, each interactive:

1. **Config** (`config.py` → `configure_defaults()`) — Interactive menu to set fonts, colors, and sizes. Persists to `config_settings.json`.

2. **Song Matching** (`search_songs.py` → `match_and_compile_songs()`) — Three-stage search engine:
   - Stage 1: Direct hymn number lookup
   - Stage 2: Substring match in title/lyrics
   - Stage 3: Fuzzy match (≥0.80 similarity threshold via `difflib.SequenceMatcher`)
   - Ambiguous matches prompt the user to pick; choices persist to `selected_songs.json`

3. **Lyrics Parsing** (`lyrics_parser.py`) — Cleans chords/metadata from raw lyrics, parses into `stanza`/`chorus` sections. Sections are detected by:
   - Bare digit lines (e.g., `1`, `2`) → stanza markers
   - Lines indented with 2+ spaces → chorus
   - Multiple lyrics versions separated by `### VersionName` headers → user picks version, persists to `version_choices.json`

4. **Alpha Ordering** (`alpha_order_songs.py` → `alpha_order()`) — Loads saved order from `song_order.json` or runs interactive reorder session.

5. **Slideshow Generation** (`slideshow.py` → `LyricsSlideshow`) — Builds a `.pptx` with:
   - Title slide
   - Lyric slides (one per section chunk, max 9 lines per slide)
   - Song list index slide (clickable grid, links to first slide of each song)
   - Alphabetical index slide
   - Home icon on every lyric slide → links back to song list slide
   - Restart icon on last slide of each song → links back to first slide of that song

## Persistent Cache Files

These files are created at runtime in the working directory and skip re-prompting on subsequent runs:

| File | Purpose |
|---|---|
| `config_settings.json` | Font, color, size settings |
| `selected_songs.json` | Song ID + display title per input line |
| `version_choices.json` | Lyrics version choice per song title |
| `song_order.json` | Alphabetical index ordering |

## Assets

`assets/home.png` and `assets/restart.png` must exist for navigation icons on slides.

## Key Data Shape

`match_and_compile_songs()` returns `(resolved_results, compiled_lyrics)` where `compiled_lyrics` is a list of tuples:
```python
(line_number: int, title: str, num_choruses: int, sections: List[Dict])
```
Each section dict has `type` (`"stanza"` or `"chorus"`), `number`, and `content`.
