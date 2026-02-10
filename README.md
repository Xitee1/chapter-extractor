# chapter-extractor

Extract recurring chapter segments (intros, outros, etc.) from large MKV collections by analyzing chapter marker patterns.

Point it at a directory of MKV files and it will find chapters that repeat across episodes with similar durations -- typically intros and outros. It extracts the video segment from the first occurrence and names the output by the episode range it covers.

## Requirements

- Python 3.12+
- [mkvtoolnix](https://mkvtoolnix.download/) (`mkvmerge` and `mkvextract` must be on PATH)

## Installation

```bash
pip install -e .
```

Or run directly:

```bash
PYTHONPATH=src python -m chapter_extractor
```

## Usage

```
chapter-extractor <input-dir> <output-dir> [options]
```

### Examples

Find recurring 90-180s chapters across at least 5 episodes (dry run):

```bash
chapter-extractor /media/anime/show ./extracted --duration-range 90-180 --dry-run
```

Extract intros/outros by chapter name:

```bash
chapter-extractor /media/anime/show ./extracted --chapter-names
```

Combine both filters (AND logic):

```bash
chapter-extractor /media/anime/show ./extracted --duration-range 80-100 --chapter-names
```

Extract all chapters of a specific length without grouping:

```bash
chapter-extractor /media/anime/show ./extracted --duration-range 85-95 --min-occurrences 0
```

Scan subdirectories and use percentage-based tolerance:

```bash
chapter-extractor /media/library ./extracted -r --duration-range 60-120 --tolerance-percent 5
```

Process non-episode files (no S##E## filename requirement):

```bash
chapter-extractor /media/movies ./extracted --no-episode-parsing --min-occurrences 0 --duration-range 60-300
```

### Options

| Option | Default | Description |
|---|---|---|
| `--duration-range MIN-MAX` | None | Filter chapters by duration in seconds |
| `--chapter-names` | Off | Filter by common names (Opening, Intro, OP, ED, Ending, Outro, Credits, Preview, Recap, Prologue, Epilogue) |
| `--min-occurrences N` | 5 | Minimum times a pattern must appear. `0` = extract all matches without grouping |
| `--tolerance-seconds N` | 2 | How close durations must be to count as "the same" |
| `--tolerance-percent N` | None | Percentage-based tolerance (mutually exclusive with `--tolerance-seconds`) |
| `--no-episode-parsing` | Off | Skip S##E## filename parsing |
| `--dry-run` | Off | Preview detected patterns without extracting |
| `--recursive`, `-r` | Off | Scan subdirectories |

If no filters are specified, all chapters are considered.

### Output

Dry run prints a summary like:

```
Scanned 847 files (12 skipped: no chapters, 3 skipped: no episode tag)

Detected patterns:
  [1] Opening (91s avg) -- S01E01-S03E24 (72 episodes)
      First occurrence: S01E01 @ 00:01:32.000 - 00:03:03.000
      Output: S01E01-S03E24_Opening.mkv

  [2] Ending (89s avg) -- S01E01-S02E12 (36 episodes)
      First occurrence: S01E01 @ 00:22:05.000 - 00:23:34.000
      Output: S01E01-S02E12_Ending.mkv
```

Extracted files are named `<episode-range>_<chapter-name>.mkv`. If the chapter has no name (or name is 1 character), duration is used instead (e.g., `S01E01-S01E12_90s.mkv`). Duplicate names get `_1`, `_2` suffixes.

## How it works

1. Scans the input directory for `.mkv` files
2. Reads chapter metadata using `mkvmerge -J` (file info) and `mkvextract --simple` (chapter timestamps)
3. Parses episode identifiers from filenames (`S01E05`, `S100E001`, etc.)
4. Filters chapters by duration range and/or chapter name
5. Clusters chapters with similar durations (within tolerance)
6. Splits clusters by episode contiguity to reduce false positives (e.g., a season 1 intro won't be grouped with a coincidentally same-length season 5 outro)
7. Extracts the segment from the first occurrence using `mkvmerge --split parts:`
