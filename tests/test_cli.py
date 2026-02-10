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
