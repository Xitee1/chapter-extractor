import os
import tempfile

from chapter_extractor.models import Chapter, EpisodeInfo, ChapterPattern
from chapter_extractor.naming import generate_output_name, format_episode_range


def _ch(season: int, episode: int, title: str | None = None, duration: float = 90.0) -> Chapter:
    return Chapter(
        start=0.0, end=duration, duration=duration,
        title=title,
        source_file=f"/fake/Show S{season:02d}E{episode:02d}.mkv",
        episode=EpisodeInfo(season, episode),
    )


def _ch_no_ep(source: str, title: str | None = None, duration: float = 90.0) -> Chapter:
    return Chapter(
        start=0.0, end=duration, duration=duration,
        title=title, source_file=source, episode=None,
    )


def test_episode_range_same_episode():
    chapters = [_ch(1, 1)]
    assert format_episode_range(chapters) == "S01E01"


def test_episode_range_same_season():
    chapters = [_ch(1, 1), _ch(1, 5), _ch(1, 12)]
    assert format_episode_range(chapters) == "S01E01-S01E12"


def test_episode_range_cross_season():
    chapters = [_ch(1, 1), _ch(2, 10)]
    assert format_episode_range(chapters) == "S01E01-S02E10"


def test_episode_range_no_episode_info():
    chapters = [_ch_no_ep("/path/to/My Movie.mkv")]
    assert format_episode_range(chapters) == "My Movie"


def test_output_name_with_title():
    chapters = [_ch(1, 1, "Opening"), _ch(1, 2, "Opening")]
    name = generate_output_name(chapters, "/tmp/out", episode_parsing=True)
    assert name == "/tmp/out/S01E01-S01E02_Opening.mkv"


def test_output_name_fallback_to_duration():
    chapters = [_ch(1, 1, None, 90.0), _ch(1, 2, None, 91.0)]
    name = generate_output_name(chapters, "/tmp/out", episode_parsing=True)
    assert name == "/tmp/out/S01E01-S01E02_90s.mkv"


def test_output_name_short_title_fallback():
    chapters = [_ch(1, 1, "X", 90.0)]
    name = generate_output_name(chapters, "/tmp/out", episode_parsing=True)
    assert name == "/tmp/out/S01E01_90s.mkv"


def test_output_name_no_episode_parsing():
    chapters = [_ch_no_ep("/path/Movie.mkv", "Intro")]
    name = generate_output_name(chapters, "/tmp/out", episode_parsing=False)
    assert name == "/tmp/out/Movie_Intro.mkv"


def test_output_name_dedup():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file that would conflict
        open(os.path.join(tmpdir, "S01E01-S01E02_Opening.mkv"), "w").close()
        chapters = [_ch(1, 1, "Opening"), _ch(1, 2, "Opening")]
        name = generate_output_name(chapters, tmpdir, episode_parsing=True)
        assert name == os.path.join(tmpdir, "S01E01-S01E02_Opening_1.mkv")


def test_output_name_sanitizes_title():
    chapters = [_ch(1, 1, "Opening / Theme")]
    name = generate_output_name(chapters, "/tmp/out", episode_parsing=True)
    assert "/" not in os.path.basename(name)
