from chapter_extractor.models import Chapter, EpisodeInfo
from chapter_extractor.matcher import filter_chapters, CHAPTER_NAME_KEYWORDS


def _ch(duration: float, title: str | None = None, season: int = 1, episode: int = 1) -> Chapter:
    """Helper to create test chapters."""
    return Chapter(
        start=0.0,
        end=duration,
        duration=duration,
        title=title,
        source_file=f"/fake/Show S{season:02d}E{episode:02d}.mkv",
        episode=EpisodeInfo(season, episode),
    )


def test_filter_by_duration_range():
    chapters = [_ch(60), _ch(90), _ch(120), _ch(180), _ch(300)]
    result = filter_chapters(chapters, duration_range=(90, 180), chapter_names=False)
    assert len(result) == 3
    assert [c.duration for c in result] == [90, 120, 180]


def test_filter_by_chapter_names():
    chapters = [
        _ch(90, "Opening"),
        _ch(90, "Episode"),
        _ch(90, "ED"),
        _ch(90, "Recap"),
        _ch(90, None),
    ]
    result = filter_chapters(chapters, duration_range=None, chapter_names=True)
    assert len(result) == 3
    titles = [c.title for c in result]
    assert "Opening" in titles
    assert "ED" in titles
    assert "Recap" in titles


def test_filter_combined_and():
    chapters = [
        _ch(90, "Opening"),
        _ch(300, "Opening"),
        _ch(90, "Episode"),
        _ch(90, None),
    ]
    result = filter_chapters(chapters, duration_range=(60, 120), chapter_names=True)
    assert len(result) == 1
    assert result[0].title == "Opening"
    assert result[0].duration == 90


def test_filter_no_filters():
    chapters = [_ch(60), _ch(90, "Opening"), _ch(300)]
    result = filter_chapters(chapters, duration_range=None, chapter_names=False)
    assert len(result) == 3


def test_filter_chapter_name_substring():
    chapters = [_ch(90, "Opening Theme"), _ch(90, "OP1"), _ch(90, "STOP")]
    result = filter_chapters(chapters, duration_range=None, chapter_names=True)
    assert len(result) == 2
    titles = [c.title for c in result]
    assert "Opening Theme" in titles
    assert "OP1" in titles


def test_filter_chapter_name_case_insensitive():
    chapters = [_ch(90, "opening"), _ch(90, "INTRO"), _ch(90, "Ending")]
    result = filter_chapters(chapters, duration_range=None, chapter_names=True)
    assert len(result) == 3
