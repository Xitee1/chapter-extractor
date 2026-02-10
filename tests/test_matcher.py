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


from chapter_extractor.matcher import cluster_by_duration


def test_cluster_by_seconds_tolerance():
    chapters = [_ch(90, episode=1), _ch(91, episode=2), _ch(92, episode=3), _ch(120, episode=4), _ch(121, episode=5)]
    clusters = cluster_by_duration(chapters, tolerance_seconds=2, tolerance_percent=None)
    assert len(clusters) == 2
    assert len(clusters[0]) == 3
    assert len(clusters[1]) == 2


def test_cluster_by_percent_tolerance():
    chapters = [_ch(100, episode=1), _ch(105, episode=2), _ch(200, episode=3), _ch(210, episode=4)]
    clusters = cluster_by_duration(chapters, tolerance_seconds=None, tolerance_percent=5)
    assert len(clusters) == 2


def test_cluster_single_chapter():
    chapters = [_ch(90)]
    clusters = cluster_by_duration(chapters, tolerance_seconds=2, tolerance_percent=None)
    assert len(clusters) == 1
    assert len(clusters[0]) == 1


def test_cluster_all_same_duration():
    chapters = [_ch(90, episode=i) for i in range(10)]
    clusters = cluster_by_duration(chapters, tolerance_seconds=2, tolerance_percent=None)
    assert len(clusters) == 1
    assert len(clusters[0]) == 10


def test_cluster_all_different():
    chapters = [_ch(60), _ch(120), _ch(180), _ch(240)]
    clusters = cluster_by_duration(chapters, tolerance_seconds=2, tolerance_percent=None)
    assert len(clusters) == 4


from chapter_extractor.matcher import split_by_contiguity
from chapter_extractor.models import Chapter


def test_contiguity_all_contiguous():
    chapters = [_ch(90, episode=i, season=1) for i in range(1, 13)]
    result = split_by_contiguity(chapters)
    assert len(result) == 1
    assert len(result[0]) == 12


def test_contiguity_gap_in_season():
    chapters = [
        _ch(90, season=1, episode=1),
        _ch(90, season=1, episode=2),
        _ch(90, season=1, episode=3),
        # gap: 4-7 missing
        _ch(90, season=1, episode=8),
        _ch(90, season=1, episode=9),
    ]
    result = split_by_contiguity(chapters)
    assert len(result) == 2
    assert len(result[0]) == 3
    assert len(result[1]) == 2


def test_contiguity_cross_season():
    chapters = [
        _ch(90, season=1, episode=11),
        _ch(90, season=1, episode=12),
        _ch(90, season=2, episode=1),
        _ch(90, season=2, episode=2),
    ]
    result = split_by_contiguity(chapters)
    assert len(result) == 1
    assert len(result[0]) == 4


def test_contiguity_season_gap():
    chapters = [
        _ch(90, season=1, episode=1),
        _ch(90, season=1, episode=2),
        _ch(90, season=3, episode=1),
        _ch(90, season=3, episode=2),
    ]
    result = split_by_contiguity(chapters)
    assert len(result) == 2


def test_contiguity_no_episode_info():
    ch1 = Chapter(start=0, end=90, duration=90, title=None, source_file="/a.mkv", episode=None)
    ch2 = Chapter(start=0, end=90, duration=90, title=None, source_file="/b.mkv", episode=None)
    result = split_by_contiguity([ch1, ch2])
    assert len(result) == 1
    assert len(result[0]) == 2


def test_contiguity_small_gap_tolerated():
    """Gaps of up to 3 episodes within a season are tolerated."""
    chapters = [
        _ch(90, season=1, episode=1),
        _ch(90, season=1, episode=2),
        _ch(90, season=1, episode=5),
        _ch(90, season=1, episode=6),
    ]
    result = split_by_contiguity(chapters)
    assert len(result) == 1
    assert len(result[0]) == 4
