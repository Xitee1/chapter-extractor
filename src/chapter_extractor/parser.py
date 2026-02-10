from __future__ import annotations

import re
from pathlib import Path

from chapter_extractor.models import EpisodeInfo

_EPISODE_RE = re.compile(r"S(\d{2,})E(\d{2,})", re.IGNORECASE)


def parse_episode(filename: str) -> EpisodeInfo | None:
    """Parse episode identifier from filename. Returns None if no match."""
    name = Path(filename).name
    match = _EPISODE_RE.search(name)
    if match is None:
        return None
    return EpisodeInfo(season=int(match.group(1)), episode=int(match.group(2)))
