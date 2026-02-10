from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EpisodeInfo:
    season: int
    episode: int

    def __lt__(self, other: EpisodeInfo) -> bool:
        return (self.season, self.episode) < (other.season, other.episode)

    def __str__(self) -> str:
        return f"S{self.season:02d}E{self.episode:02d}"


@dataclass
class Chapter:
    start: float
    end: float
    duration: float
    title: str | None
    source_file: str
    episode: EpisodeInfo | None = None


@dataclass
class ChapterPattern:
    chapters: list[Chapter]
    avg_duration: float
    episode_range: str
    first_occurrence: Chapter
    output_name: str = ""
