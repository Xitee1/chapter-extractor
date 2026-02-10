from unittest.mock import patch, MagicMock
import subprocess

from chapter_extractor.chapters import read_chapters


SAMPLE_SIMPLE_CHAPTERS = """\
CHAPTER01=00:00:00.000
CHAPTER01NAME=Intro
CHAPTER02=00:01:30.000
CHAPTER02NAME=Episode
CHAPTER03=00:23:00.000
CHAPTER03NAME=Ending
"""

SAMPLE_MKVMERGE_JSON = """{
  "chapters": [{"num_entries": 3}],
  "container": {
    "properties": {"duration": 1440000000000}
  }
}"""

SAMPLE_MKVMERGE_JSON_NO_CHAPTERS = """{
  "chapters": [],
  "container": {
    "properties": {"duration": 1440000000000}
  }
}"""

SAMPLE_SIMPLE_NO_NAMES = """\
CHAPTER01=00:00:00.000
CHAPTER01NAME=
CHAPTER02=00:05:00.000
CHAPTER02NAME=
"""


@patch("chapter_extractor.chapters._read_simple_chapters")
@patch("subprocess.run")
def test_read_chapters_basic(mock_run, mock_read_simple):
    mock_run.return_value = MagicMock(returncode=0, stdout=SAMPLE_MKVMERGE_JSON)
    mock_read_simple.return_value = SAMPLE_SIMPLE_CHAPTERS

    chapters = read_chapters("/fake/Show S01E01.mkv")

    assert len(chapters) == 3
    assert chapters[0].title == "Intro"
    assert chapters[0].start == 0.0
    assert chapters[0].end == 90.0
    assert chapters[0].duration == 90.0
    assert chapters[1].title == "Episode"
    assert chapters[1].start == 90.0
    assert chapters[1].end == 1380.0
    assert chapters[2].title == "Ending"
    assert chapters[2].start == 1380.0
    assert chapters[2].end == 1440.0
    assert chapters[2].duration == 60.0


@patch("chapter_extractor.chapters._read_simple_chapters")
@patch("subprocess.run")
def test_read_chapters_no_chapters(mock_run, mock_read_simple):
    mock_run.return_value = MagicMock(returncode=0, stdout=SAMPLE_MKVMERGE_JSON_NO_CHAPTERS)

    chapters = read_chapters("/fake/movie.mkv")

    assert chapters == []
    mock_read_simple.assert_not_called()


@patch("chapter_extractor.chapters._read_simple_chapters")
@patch("subprocess.run")
def test_read_chapters_empty_names(mock_run, mock_read_simple):
    mock_run.return_value = MagicMock(returncode=0, stdout=SAMPLE_MKVMERGE_JSON)
    mock_read_simple.return_value = SAMPLE_SIMPLE_NO_NAMES

    chapters = read_chapters("/fake/Show S01E01.mkv")

    assert len(chapters) == 2
    assert chapters[0].title is None
    assert chapters[1].title is None


@patch("subprocess.run")
def test_read_chapters_mkvmerge_fails(mock_run):
    mock_run.side_effect = FileNotFoundError("mkvmerge not found")

    chapters = read_chapters("/fake/file.mkv")
    assert chapters is None


@patch("subprocess.run")
def test_read_chapters_corrupt_file(mock_run):
    mock_run.return_value = MagicMock(returncode=2, stdout="", stderr="Error: file corrupt")

    chapters = read_chapters("/fake/file.mkv")
    assert chapters is None


def test_parse_timestamp():
    from chapter_extractor.chapters import _parse_timestamp
    assert _parse_timestamp("00:00:00.000") == 0.0
    assert _parse_timestamp("00:01:30.000") == 90.0
    assert _parse_timestamp("01:00:00.000") == 3600.0
    assert _parse_timestamp("00:00:00.500") == 0.5


def test_format_timestamp():
    from chapter_extractor.chapters import format_timestamp
    assert format_timestamp(0.0) == "00:00:00.000"
    assert format_timestamp(90.0) == "00:01:30.000"
    assert format_timestamp(3600.0) == "01:00:00.000"
    assert format_timestamp(90.5) == "00:01:30.500"
