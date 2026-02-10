from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

from chapter_extractor.models import Chapter

_CHAPTER_RE = re.compile(r"CHAPTER(\d+)=(.+)")
_CHAPTER_NAME_RE = re.compile(r"CHAPTER(\d+)NAME=(.*)")


def _parse_timestamp(ts: str) -> float:
    """Convert HH:MM:SS.mmm to seconds."""
    parts = ts.strip().split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def format_timestamp(s: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format."""
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = s % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def _get_file_info(mkv_path: str) -> tuple[int, float] | None:
    """Get chapter count and duration from mkvmerge -J. Returns None on error."""
    try:
        result = subprocess.run(
            ["mkvmerge", "-J", mkv_path],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("Error: mkvmerge not found. Install mkvtoolnix.", file=sys.stderr)
        return None
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    chapters = data.get("chapters", [])
    num_chapters = chapters[0]["num_entries"] if chapters else 0
    duration_ns = data["container"]["properties"]["duration"]
    duration_s = duration_ns / 1_000_000_000
    return num_chapters, duration_s


def _read_simple_chapters(mkv_path: str) -> str | None:
    """Run mkvextract to get simple chapter format. Returns content or None."""
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".txt")
    os.close(tmp_fd)
    try:
        result = subprocess.run(
            ["mkvextract", mkv_path, "chapters", "--simple", tmp_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        with open(tmp_path) as f:
            return f.read()
    finally:
        os.unlink(tmp_path)


def _parse_simple_format(content: str, file_duration: float, source_file: str) -> list[Chapter]:
    """Parse mkvextract --simple output into Chapter objects."""
    timestamps: dict[str, float] = {}
    names: dict[str, str] = {}

    for line in content.strip().splitlines():
        m = _CHAPTER_RE.match(line)
        if m:
            timestamps[m.group(1)] = _parse_timestamp(m.group(2))
            continue
        m = _CHAPTER_NAME_RE.match(line)
        if m:
            name = m.group(2).strip()
            names[m.group(1)] = name if len(name) >= 1 else ""

    sorted_ids = sorted(timestamps.keys())
    chapters: list[Chapter] = []

    for i, chap_id in enumerate(sorted_ids):
        start = timestamps[chap_id]
        if i + 1 < len(sorted_ids):
            end = timestamps[sorted_ids[i + 1]]
        else:
            end = file_duration
        title_raw = names.get(chap_id, "")
        title = title_raw if title_raw else None
        chapters.append(Chapter(
            start=start,
            end=end,
            duration=end - start,
            title=title,
            source_file=source_file,
        ))

    return chapters


def read_chapters(mkv_path: str) -> list[Chapter] | None:
    """Read chapters from MKV file. Returns [] if no chapters, None on error."""
    info = _get_file_info(mkv_path)
    if info is None:
        return None
    num_chapters, duration = info
    if num_chapters == 0:
        return []

    content = _read_simple_chapters(mkv_path)
    if content is None:
        return None

    return _parse_simple_format(content, duration, mkv_path)
