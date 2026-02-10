from unittest.mock import patch, MagicMock, call

from chapter_extractor.models import Chapter, EpisodeInfo
from chapter_extractor.extractor import extract_segment


def _ch(start: float, end: float) -> Chapter:
    return Chapter(
        start=start, end=end, duration=end - start,
        title="Opening", source_file="/fake/Show S01E01.mkv",
        episode=EpisodeInfo(1, 1),
    )


@patch("subprocess.run")
def test_extract_segment_basic(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    chapter = _ch(90.0, 180.0)

    result = extract_segment(chapter, "/tmp/out/S01E01-S01E12_Opening.mkv")

    assert result is True
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "mkvmerge"
    assert "--split" in cmd
    assert "parts:00:01:30.000-00:03:00.000" in cmd
    assert "-o" in cmd


@patch("subprocess.run")
def test_extract_segment_failure(mock_run):
    mock_run.return_value = MagicMock(returncode=2, stderr="Error")
    chapter = _ch(0.0, 90.0)

    result = extract_segment(chapter, "/tmp/out.mkv")

    assert result is False


@patch("subprocess.run")
def test_extract_segment_creates_output_dir(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    chapter = _ch(0.0, 90.0)

    with patch("os.makedirs") as mock_makedirs:
        extract_segment(chapter, "/tmp/new_dir/out.mkv")
        mock_makedirs.assert_called_once_with("/tmp/new_dir", exist_ok=True)
