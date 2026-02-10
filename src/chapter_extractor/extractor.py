from __future__ import annotations

import os
import subprocess
import sys

from chapter_extractor.chapters import format_timestamp
from chapter_extractor.models import Chapter


def extract_segment(chapter: Chapter, output_path: str) -> bool:
    """Extract a chapter segment from MKV file. Returns True on success."""
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    start_ts = format_timestamp(chapter.start)
    end_ts = format_timestamp(chapter.end)

    try:
        result = subprocess.run(
            [
                "mkvmerge",
                "-o", output_path,
                "--split", f"parts:{start_ts}-{end_ts}",
                chapter.source_file,
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("Error: mkvmerge not found. Install mkvtoolnix.", file=sys.stderr)
        return False

    if result.returncode not in (0, 1):
        # mkvmerge returns 1 for warnings, 2 for errors
        print(f"Error extracting {output_path}: {result.stderr}", file=sys.stderr)
        return False

    return True
