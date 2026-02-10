from __future__ import annotations

import os
import re
from collections import Counter
from pathlib import Path

from chapter_extractor.models import Chapter


def format_episode_range(chapters: list[Chapter]) -> str:
    """Format episode range from chapters. Falls back to source filename."""
    episodes = [c.episode for c in chapters if c.episode is not None]
    if not episodes:
        return Path(chapters[0].source_file).stem

    sorted_eps = sorted(episodes)
    first = sorted_eps[0]
    last = sorted_eps[-1]
    if first == last:
        return str(first)
    return f"{first}-{last}"


def _sanitize_filename(name: str) -> str:
    """Remove characters unsafe for filenames."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()


def _get_chapter_identifier(chapters: list[Chapter]) -> str:
    """Get chapter identifier: title if len >= 2, else average duration."""
    titles = [c.title for c in chapters if c.title and len(c.title) >= 2]
    if titles:
        most_common = Counter(titles).most_common(1)[0][0]
        return _sanitize_filename(most_common)
    avg_duration = sum(c.duration for c in chapters) / len(chapters)
    return f"{int(avg_duration)}s"


def generate_output_name(
    chapters: list[Chapter],
    output_dir: str,
    episode_parsing: bool,
) -> str:
    """Generate unique output filename for a chapter pattern."""
    if episode_parsing:
        range_part = format_episode_range(chapters)
    else:
        range_part = Path(chapters[0].source_file).stem

    identifier = _get_chapter_identifier(chapters)
    base_name = f"{range_part}_{identifier}"
    output_path = os.path.join(output_dir, f"{base_name}.mkv")

    # Deduplicate
    counter = 1
    while os.path.exists(output_path):
        output_path = os.path.join(output_dir, f"{base_name}_{counter}.mkv")
        counter += 1

    return output_path
