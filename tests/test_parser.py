from chapter_extractor.parser import parse_episode


def test_standard_format():
    result = parse_episode("Show Name S01E05 720p.mkv")
    assert result is not None
    assert result.season == 1
    assert result.episode == 5


def test_three_digit_format():
    result = parse_episode("Show S100E001.mkv")
    assert result is not None
    assert result.season == 100
    assert result.episode == 1


def test_case_insensitive():
    result = parse_episode("show s02e10.mkv")
    assert result is not None
    assert result.season == 2
    assert result.episode == 10


def test_no_episode_tag():
    result = parse_episode("random_movie.mkv")
    assert result is None


def test_path_with_directories():
    result = parse_episode("/media/shows/Show Name S03E12 1080p.mkv")
    assert result is not None
    assert result.season == 3
    assert result.episode == 12


def test_episode_info_str():
    result = parse_episode("Show S01E05.mkv")
    assert str(result) == "S01E05"


def test_episode_info_str_large_numbers():
    result = parse_episode("Show S100E001.mkv")
    assert str(result) == "S100E01"


def test_episode_info_sorting():
    a = parse_episode("Show S01E05.mkv")
    b = parse_episode("Show S01E10.mkv")
    c = parse_episode("Show S02E01.mkv")
    assert a < b < c
