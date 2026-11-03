"""Command-line entry point for indexing events and rendering basketball clips."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from agent.clip_planner import plan_clips
from agent.query_parser import parse_query
from index.event_index import EventIndex
from render.ffmpeg_renderer import probe_video, render_clips


class Diagnostics:
    """Append structured recoverable and fatal errors to a JSONL file."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, entry: dict) -> None:
        payload = {"logged_at": datetime.now(timezone.utc).isoformat(), **entry}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")


def build_parser() -> argparse.ArgumentParser:
    """Build the sports clip CLI argument parser."""
    parser = argparse.ArgumentParser(description="Plan and render basketball highlight clips from events.jsonl")
    parser.add_argument("--video", required=True, type=Path, help="source match video")
    parser.add_argument("--events", required=True, type=Path, help="CV event JSONL file")
    parser.add_argument("--query", required=True, help="for example: 'all scoring plays' or '最后5分钟关键时刻'")
    parser.add_argument("--output-dir", type=Path, default=Path("sports-clips"))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true", help="write manifest and low-bitrate preview MP4")
    mode.add_argument("--render", action="store_true", help="write manifest and final highlights MP4")
    parser.add_argument("--padding-seconds", type=float, default=3.0, help="context before and after each event")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run event query, manifest generation, and FFmpeg rendering."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    diagnostics = Diagnostics(args.output_dir / "diagnostics.jsonl")
    mode = "preview" if args.preview else "render"
    try:
        if not args.video.is_file():
            raise FileNotFoundError(f"video not found: {args.video}")
        if not args.events.is_file():
            raise FileNotFoundError(f"events file not found: {args.events}")
        fps, duration = probe_video(args.video)
        index = EventIndex.from_jsonl(args.events, diagnostics)
        query = parse_query(args.query)
        clips = plan_clips(index, query, fps, duration, args.padding_seconds)
        manifest = {
            "video": str(args.video.resolve()), "fps": fps, "duration_seconds": duration,
            "query": args.query, "mode": mode, "padding_seconds": args.padding_seconds,
            "clips": [clip.to_dict() for clip in clips],
        }
        manifest_path = args.output_dir / "clips.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not clips:
            raise ValueError("query matched no events; clips.json was written with an empty clip list")
        rendered = render_clips(args.video, clips, args.output_dir, mode, diagnostics)
        logging.info("wrote %d clip(s) to %s and %s", len(clips), manifest_path, rendered)
        return 0
    except Exception as exc:
        diagnostics({"stage": "cli", "timestamp": None, "reason": str(exc), "recovered": False})
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
