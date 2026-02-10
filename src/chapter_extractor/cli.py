from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from chapter_extractor.chapters import read_chapters, format_timestamp
from chapter_extractor.extractor import extract_segment
from chapter_extractor.matcher import (
    cluster_by_duration,
    filter_chapters,
    split_by_contiguity,
    split_duplicate_episodes,
)
from chapter_extractor.models import Chapter, ChapterPattern
from chapter_extractor.naming import (
    format_episode_range,
    generate_output_name,
)
from chapter_extractor.parser import parse_episode


def _parse_duration_range(value: str) -> tuple[float, float]:
    """Parse duration range string like '120-240' into (min, max) seconds."""
    parts = value.split("-")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(f"Invalid duration range: {value}. Use format: MIN-MAX (e.g., 120-240)")
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid duration range: {value}. Values must be numbers.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="chapter-extractor",
        description="Extract recurring chapter segments from MKV collections.",
    )
    parser.add_argument("input_dir", help="Directory to scan for MKV files")
    parser.add_argument("output_dir", help="Directory for extracted segments")
    parser.add_argument(
        "--duration-range",
        type=_parse_duration_range,
        default=None,
        help="Duration range in seconds (e.g., 120-240)",
    )
    parser.add_argument(
        "--chapter-names",
        action="store_true",
        help="Filter by predefined chapter name keywords",
    )
    parser.add_argument(
        "--min-occurrences",
        type=int,
        default=5,
        help="Minimum occurrences for a pattern (0 = extract all matches). Default: 5",
    )

    tol_group = parser.add_mutually_exclusive_group()
    tol_group.add_argument(
        "--tolerance-seconds",
        type=float,
        default=None,
        help="Absolute duration tolerance in seconds. Default: 2",
    )
    tol_group.add_argument(
        "--tolerance-percent",
        type=float,
        default=None,
        help="Percentage duration tolerance (mutually exclusive with --tolerance-seconds)",
    )

    parser.add_argument(
        "--no-episode-parsing",
        action="store_true",
        help="Disable episode tag parsing from filenames",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview detected patterns without extracting",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Scan subdirectories",
    )

    args = parser.parse_args(argv)

    # Default tolerance
    if args.tolerance_seconds is None and args.tolerance_percent is None:
        args.tolerance_seconds = 2.0

    # Flip no-episode-parsing to episode_parsing
    args.episode_parsing = not args.no_episode_parsing
    del args.no_episode_parsing

    return args


def _scan_directory(input_dir: str, recursive: bool) -> list[str]:
    """Find all .mkv files in directory."""
    pattern = "**/*.mkv" if recursive else "*.mkv"
    return sorted(str(p) for p in Path(input_dir).glob(pattern))


def _build_patterns(
    clusters: list[list[Chapter]],
    output_dir: str,
    episode_parsing: bool,
) -> list[ChapterPattern]:
    """Build ChapterPattern objects from clusters."""
    patterns: list[ChapterPattern] = []
    for cluster in clusters:
        if episode_parsing:
            sorted_cluster = sorted(
                cluster,
                key=lambda c: (c.episode.season, c.episode.episode) if c.episode else (0, 0),
            )
        else:
            sorted_cluster = cluster

        first = sorted_cluster[0]
        avg_dur = sum(c.duration for c in cluster) / len(cluster)
        ep_range = format_episode_range(cluster)
        output_name = generate_output_name(cluster, output_dir, episode_parsing)

        patterns.append(ChapterPattern(
            chapters=sorted_cluster,
            avg_duration=avg_dur,
            episode_range=ep_range,
            first_occurrence=first,
            output_name=output_name,
        ))
    return patterns


def _print_summary(
    patterns: list[ChapterPattern],
    total_files: int,
    skipped_no_chapters: int,
    skipped_no_episode: int,
) -> None:
    """Print detection summary."""
    print(f"\nScanned {total_files} files", end="")
    skips = []
    if skipped_no_chapters > 0:
        skips.append(f"{skipped_no_chapters} skipped: no chapters")
    if skipped_no_episode > 0:
        skips.append(f"{skipped_no_episode} skipped: no episode tag")
    if skips:
        print(f" ({', '.join(skips)})")
    else:
        print()

    if not patterns:
        print("\nNo matching patterns detected.")
        return

    print(f"\nDetected patterns:")
    for i, pattern in enumerate(patterns, 1):
        title = pattern.first_occurrence.title or f"{int(pattern.avg_duration)}s"
        print(f"  [{i}] {title} ({int(pattern.avg_duration)}s avg) — {pattern.episode_range} ({len(pattern.chapters)} episodes)")
        first = pattern.first_occurrence
        ep_str = str(first.episode) if first.episode else Path(first.source_file).stem
        print(f"      First occurrence: {ep_str} @ {format_timestamp(first.start)} - {format_timestamp(first.end)}")
        print(f"      Output: {os.path.basename(pattern.output_name)}")
    print()


def run(args: argparse.Namespace) -> int:
    """Main pipeline."""
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        return 1

    # Step 1: Scan
    mkv_files = _scan_directory(args.input_dir, args.recursive)
    if not mkv_files:
        print(f"No .mkv files found in {args.input_dir}", file=sys.stderr)
        return 1

    # Step 2: Read chapters and parse episodes
    all_chapters: list[Chapter] = []
    skipped_no_chapters = 0
    skipped_no_episode = 0

    for mkv_path in mkv_files:
        chapters = read_chapters(mkv_path)
        if chapters is None:
            print(f"Warning: Could not read {mkv_path}, skipping.", file=sys.stderr)
            skipped_no_chapters += 1
            continue
        if not chapters:
            print(f"Warning: No chapters in {mkv_path}, skipping.", file=sys.stderr)
            skipped_no_chapters += 1
            continue

        if args.episode_parsing:
            episode = parse_episode(mkv_path)
            if episode is None:
                print(f"Warning: No episode tag in {os.path.basename(mkv_path)}, skipping.", file=sys.stderr)
                skipped_no_episode += 1
                continue
            for ch in chapters:
                ch.episode = episode

        all_chapters.extend(chapters)

    if not all_chapters:
        print("No chapters found in any files.", file=sys.stderr)
        return 1

    # Step 3: Filter
    filtered = filter_chapters(all_chapters, args.duration_range, args.chapter_names)
    if not filtered:
        print("No chapters match the specified filters.", file=sys.stderr)
        return 1

    # Step 4: Group
    if args.min_occurrences > 0:
        clusters = cluster_by_duration(filtered, args.tolerance_seconds, args.tolerance_percent)

        # Split clusters where the same episode appears multiple times
        deduped: list[list[Chapter]] = []
        for cluster in clusters:
            deduped.extend(split_duplicate_episodes(cluster))
        clusters = deduped

        if args.episode_parsing:
            split_clusters: list[list[Chapter]] = []
            for cluster in clusters:
                split_clusters.extend(split_by_contiguity(cluster))
            clusters = split_clusters

        clusters = [c for c in clusters if len(c) >= args.min_occurrences]
    else:
        clusters = [[ch] for ch in filtered]

    if not clusters:
        print("No patterns meet the minimum occurrence threshold.", file=sys.stderr)
        return 1

    # Step 5: Build patterns and print summary
    os.makedirs(args.output_dir, exist_ok=True)
    patterns = _build_patterns(clusters, args.output_dir, args.episode_parsing)
    _print_summary(patterns, len(mkv_files), skipped_no_chapters, skipped_no_episode)

    # Step 6: Extract (unless dry run)
    if args.dry_run:
        return 0

    success = 0
    fail = 0
    for pattern in patterns:
        print(f"Extracting: {os.path.basename(pattern.output_name)}...", end=" ", flush=True)
        if extract_segment(pattern.first_occurrence, pattern.output_name):
            print("OK")
            success += 1
        else:
            print("FAILED")
            fail += 1

    print(f"\nDone. {success} extracted, {fail} failed.")
    return 0 if fail == 0 else 1


def main() -> None:
    args = parse_args()
    sys.exit(run(args))
