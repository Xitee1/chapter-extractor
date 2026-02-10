from __future__ import annotations

import re

from chapter_extractor.models import Chapter, EpisodeInfo

CHAPTER_NAME_KEYWORDS: list[str] = [
    "opening", "intro", "op",
    "ending", "outro", "ed",
    "credits", "preview", "recap",
    "prologue", "epilogue",
]

_KEYWORD_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in CHAPTER_NAME_KEYWORDS) + r")",
    re.IGNORECASE,
)


def _matches_chapter_name(title: str) -> bool:
    """Check if title matches any predefined chapter name keyword."""
    return _KEYWORD_PATTERN.search(title) is not None


def filter_chapters(
    chapters: list[Chapter],
    duration_range: tuple[float, float] | None,
    chapter_names: bool,
) -> list[Chapter]:
    """Filter chapters by duration range and/or chapter names. Filters are AND when combined."""
    result = chapters

    if duration_range is not None:
        min_dur, max_dur = duration_range
        result = [c for c in result if min_dur <= c.duration <= max_dur]

    if chapter_names:
        result = [c for c in result if c.title and _matches_chapter_name(c.title)]

    return result


def cluster_by_duration(
    chapters: list[Chapter],
    tolerance_seconds: float | None,
    tolerance_percent: float | None,
) -> list[list[Chapter]]:
    """Group chapters with similar durations using single-linkage clustering."""
    if not chapters:
        return []

    sorted_chapters = sorted(chapters, key=lambda c: c.duration)
    clusters: list[list[Chapter]] = [[sorted_chapters[0]]]

    for chapter in sorted_chapters[1:]:
        prev = clusters[-1][-1]
        if tolerance_seconds is not None:
            similar = abs(chapter.duration - prev.duration) <= tolerance_seconds
        else:
            similar = abs(chapter.duration - prev.duration) / prev.duration * 100 <= tolerance_percent
        if similar:
            clusters[-1].append(chapter)
        else:
            clusters.append([chapter])

    return clusters
