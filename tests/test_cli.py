import sys
from unittest.mock import patch

from chapter_extractor.cli import parse_args


def test_parse_args_minimal():
    args = parse_args(["/input", "/output"])
    assert args.input_dir == "/input"
    assert args.output_dir == "/output"
    assert args.duration_range is None
    assert args.chapter_names is False
    assert args.min_occurrences == 5
    assert args.tolerance_seconds == 2.0
    assert args.tolerance_percent is None
    assert args.episode_parsing is True
    assert args.dry_run is False
    assert args.recursive is False


def test_parse_args_duration_range():
    args = parse_args(["/in", "/out", "--duration-range", "120-240"])
    assert args.duration_range == (120.0, 240.0)


def test_parse_args_all_options():
    args = parse_args([
        "/in", "/out",
        "--duration-range", "90-180",
        "--chapter-names",
        "--min-occurrences", "3",
        "--tolerance-percent", "5",
        "--no-episode-parsing",
        "--dry-run",
        "--recursive",
    ])
    assert args.duration_range == (90.0, 180.0)
    assert args.chapter_names is True
    assert args.min_occurrences == 3
    assert args.tolerance_percent == 5.0
    assert args.tolerance_seconds is None
    assert args.episode_parsing is False
    assert args.dry_run is True
    assert args.recursive is True


def test_parse_args_tolerance_mutual_exclusion():
    """Cannot specify both tolerance-seconds and tolerance-percent."""
    with patch("sys.stderr"):
        try:
            parse_args(["/in", "/out", "--tolerance-seconds", "2", "--tolerance-percent", "5"])
            assert False, "Should have raised SystemExit"
        except SystemExit:
            pass


from unittest.mock import patch, MagicMock
from chapter_extractor.cli import run, parse_args


@patch("chapter_extractor.cli.extract_segment")
@patch("chapter_extractor.cli.read_chapters")
@patch("chapter_extractor.cli._scan_directory")
@patch("os.path.isdir", return_value=True)
def test_pipeline_dry_run(mock_isdir, mock_scan, mock_read, mock_extract, tmp_path):
    """Full pipeline test with dry run."""
    from chapter_extractor.models import Chapter, EpisodeInfo

    mock_scan.return_value = [
        f"/fake/Show S01E{i:02d}.mkv" for i in range(1, 11)
    ]

    def make_chapters(path):
        return [
            Chapter(start=0.0, end=90.0, duration=90.0, title="Opening",
                    source_file=path),
            Chapter(start=90.0, end=1200.0, duration=1110.0, title="Episode",
                    source_file=path),
            Chapter(start=1200.0, end=1290.0, duration=90.0, title="Ending",
                    source_file=path),
        ]

    mock_read.side_effect = make_chapters

    args = parse_args([
        "/fake/input", str(tmp_path),
        "--duration-range", "60-120",
        "--min-occurrences", "5",
        "--dry-run",
    ])
    result = run(args)

    assert result == 0
    mock_extract.assert_not_called()


@patch("chapter_extractor.cli.extract_segment")
@patch("chapter_extractor.cli.read_chapters")
@patch("chapter_extractor.cli._scan_directory")
@patch("os.path.isdir", return_value=True)
def test_pipeline_extract(mock_isdir, mock_scan, mock_read, mock_extract, tmp_path):
    """Full pipeline test with extraction."""
    from chapter_extractor.models import Chapter

    mock_scan.return_value = [
        f"/fake/Show S01E{i:02d}.mkv" for i in range(1, 11)
    ]

    def make_chapters(path):
        return [
            Chapter(start=0.0, end=90.0, duration=90.0, title="Opening",
                    source_file=path),
        ]

    mock_read.side_effect = make_chapters
    mock_extract.return_value = True

    args = parse_args([
        "/fake/input", str(tmp_path),
        "--duration-range", "60-120",
        "--min-occurrences", "5",
    ])
    result = run(args)

    assert result == 0
    assert mock_extract.call_count >= 1
