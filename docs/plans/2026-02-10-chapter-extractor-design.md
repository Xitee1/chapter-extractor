# Chapter Extractor — Design Document

## Overview

CLI tool to extract recurring chapter segments (intros, outros, etc.) from large collections of MKV files. Identifies chapters that appear across multiple episodes by matching duration, optionally filters by chapter name, and extracts the video segment from the first occurrence.

## Tech Stack

- Python 3.12+ (no external dependencies)
- argparse for CLI
- mkvtoolnix (`mkvmerge`) for chapter reading and segment extraction
- In-memory processing only (no persistent cache)

## Project Structure

```
chapter-extractor/
├── pyproject.toml
├── src/
│   └── chapter_extractor/
│       ├── __init__.py
│       ├── __main__.py       # python -m chapter_extractor
│       ├── cli.py             # argparse setup & main entry point
│       ├── parser.py          # episode filename parsing (S##E##)
│       ├── chapters.py        # mkvtoolnix chapter reading
│       ├── matcher.py         # duration grouping, filtering, clustering
│       └── extractor.py       # mkvmerge segment extraction
```

## CLI Interface

```
chapter-extractor <input-dir> <output-dir> [options]
```

### Required

| Argument      | Description              |
|---------------|--------------------------|
| `input-dir`   | Directory to scan for MKV files |
| `output-dir`  | Directory for extracted segments |

### Optional

| Argument                | Default | Description |
|-------------------------|---------|-------------|
| `--duration-range`      | None    | Duration range in seconds, e.g. `120-240` |
| `--chapter-names`       | Off     | Filter by predefined common chapter names |
| `--min-occurrences`     | `5`     | Minimum times a chapter pattern must appear. `0` = extract all matches without grouping |
| `--tolerance-seconds`   | `2`     | Absolute tolerance for duration matching |
| `--tolerance-percent`   | None    | Percentage tolerance (mutually exclusive with `--tolerance-seconds`) |
| `--no-episode-parsing`  | Off     | Disable episode tag parsing (for non-episode files) |
| `--dry-run`             | Off     | Preview matches without extracting |
| `--recursive`           | Off     | Scan subdirectories |

### Filter combinability

- No filters: all chapters are candidates.
- `--duration-range` only: filter by duration.
- `--chapter-names` only: filter by name.
- Both: AND (must match both).
- Tolerance is only relevant when `--min-occurrences > 0`.

## Core Algorithm

### Step 1 — Scan & Parse

- Walk `input-dir` for `.mkv` files (optionally recursive).
- If episode parsing is enabled: parse episode identifiers from filenames using regex `S(\d{2,})E(\d{2,})` (case-insensitive, supports any digit count).
- Files without a valid episode tag: warn and process without episode metadata.
- Files with no chapters: warn and skip.

### Step 2 — Extract Chapter Metadata

- For each MKV, run: `mkvmerge --identify --identification-format json <file>`
- Parse JSON output for chapter entries: start timestamp, end timestamp, title.
- Store in memory as `Chapter` objects tied to their source file and episode info.

### Step 3 — Filter

- If `--duration-range`: keep only chapters within range.
- If `--chapter-names`: keep only chapters whose title matches the predefined list (case-insensitive, substring match).
- If neither: keep all.

### Step 4 — Group (when `min-occurrences > 0`)

- Sort remaining chapters by duration.
- Cluster chapters whose durations fall within tolerance of each other.
- If episode parsing is enabled: within each cluster, check for contiguous episode ranges. Split non-contiguous runs into separate sub-clusters.
- Discard clusters below `--min-occurrences` threshold.
- Each surviving cluster = one detected pattern.

### Step 5 — Extract

- For each detected pattern (or each matching chapter if `min-occurrences=0`):
  - Use `mkvmerge` to split the segment from the **first occurrence** using its exact timestamps.
  - Write to output directory with appropriate naming.

## Episode Parser

- Regex: `S(\d{2,})E(\d{2,})` (case-insensitive)
- Extracts season and episode numbers as integers.
- Supports: `S01E01`, `S100E001`, etc.
- Returns `None` for non-matching filenames.
- Controlled by `--no-episode-parsing` flag (default: enabled).

## Season-Aware False Positive Reduction

When episode parsing is enabled and `min-occurrences > 0`:

After clustering by duration, verify that episodes within a cluster form contiguous ranges. If not, split into sub-clusters of contiguous runs.

Example:
- Cluster of 90s chapters in: S01E01-S01E12, S02E01-S02E10, S05E03, S05E07
- Split into: `S01E01-S02E10` (contiguous) and `S05E03, S05E07` (separate, may fall below threshold)

One duration cluster can produce multiple output files.

## Predefined Chapter Names

Used when `--chapter-names` is specified. Case-insensitive substring matching.

```
Opening, Intro, OP, ED, Ending, Outro,
Credits, Preview, Recap, Prologue, Epilogue
```

"Opening Theme" and "OP1" would both match.

## Output Naming

### Format

`<episode-range>_<chapter-identifier>.mkv`

### Chapter identifier (priority order)

1. Chapter title if present and `len >= 2` (e.g., `Opening`, `ED`)
2. Fall back to duration in seconds (e.g., `120s`)

### Episode range

- Episode parsing enabled: `S01E01-S02E05`
- Episode parsing disabled: source filename (without extension)

### Duplicate handling

- If two clusters produce the same name for the same episode range, append `_1`, `_2`, etc.
- Example: `S01E01-S02E05_Theme_1.mkv`, `S01E01-S02E05_Theme_2.mkv`
- Always check file existence before writing — never overwrite.

## Dry Run Output

```
Scanned 847 files (12 skipped: no chapters, 3 skipped: no episode tag)

Detected patterns:
  [1] Opening (91s avg) — S01E01-S03E24 (72 episodes)
      First occurrence: S01E01 @ 00:01:32 - 00:03:03
      Output: S01E01-S03E24_Opening.mkv

  [2] Ending (89s avg) — S01E01-S02E12 (36 episodes)
      First occurrence: S01E01 @ 00:22:05 - 00:23:34
      Output: S01E01-S02E12_Ending.mkv

  [3] Opening (87s avg) — S04E01-S04E12 (12 episodes)
      First occurrence: S04E01 @ 00:00:00 - 00:01:27
      Output: S04E01-S04E12_Opening.mkv
```

Non-dry-run mode prints the same summary, then extracts with progress output.

## Error Handling

- `mkvmerge` not found on PATH: exit with clear error message to install mkvtoolnix.
- Corrupt/unreadable MKV: warn and skip, continue with remaining files.
- MKV with no chapters: warn and skip.
- Files without episode tags (when parsing enabled): warn and skip.

## mkvmerge Commands

Reading chapters:
```
mkvmerge --identify --identification-format json <file>
```

Extracting segments:
```
mkvmerge --split timestamps:<start>,<end> -o <output> <input>
```
