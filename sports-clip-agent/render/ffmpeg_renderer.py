"""Render planned source intervals as preview or concatenated MP4 output."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from agent.clip_planner import ClipSegment


def probe_video(path: str | Path) -> tuple[float, float]:
    """Return (frames_per_second, duration_seconds) using ffprobe metadata."""
    executable = shutil.which("ffprobe")
    if not executable:
        raise RuntimeError("ffprobe was not found on PATH; install FFmpeg and retry")
    command = [executable, "-v", "error", "-select_streams", "v:0", "-show_entries",
               "stream=avg_frame_rate,duration:format=duration", "-of", "json", str(path)]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    metadata = json.loads(result.stdout)
    streams = metadata.get("streams", [])
    if not streams:
        raise ValueError("input contains no video stream")
    fps = _fraction(streams[0].get("avg_frame_rate", "0/1"))
    duration = float(streams[0].get("duration") or metadata.get("format", {}).get("duration") or 0)
    if fps <= 0 or duration <= 0:
        raise ValueError("ffprobe returned invalid video frame rate or duration")
    return fps, duration


def render_clips(video: str | Path, clips: list[ClipSegment], output_dir: str | Path,
                 mode: str, diagnostics=None) -> Path:
    """Render clip segments and return the preview or final MP4 path."""
    if mode not in {"preview", "render"}:
        raise ValueError("mode must be 'preview' or 'render'")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg was not found on PATH; install FFmpeg and retry")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    if not clips:
        raise ValueError("query produced no clips")
    intermediates = destination / ("preview_segments" if mode == "preview" else "render_segments")
    intermediates.mkdir(exist_ok=True)
    rendered: list[Path] = []
    for index, clip in enumerate(clips, 1):
        segment = intermediates / f"clip_{index:03d}.mp4"
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{clip.start_seconds:.6f}",
                   "-i", str(video), "-t", f"{clip.end_seconds - clip.start_seconds:.6f}",
                   "-map", "0:v:0", "-map", "0:a?", "-c:v", "libx264",
                   "-preset", "veryfast" if mode == "preview" else "medium",
                   "-b:v", "600k" if mode == "preview" else "2500k", "-c:a", "aac", "-b:a", "96k", str(segment)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            rendered.append(segment)
        except (subprocess.CalledProcessError, OSError) as exc:
            message = getattr(exc, "stderr", None) or str(exc)
            _record(diagnostics, {"stage": "renderer", "timestamp": clip.start_seconds,
                                  "frame": clip.start_frame, "reason": message.strip(), "recovered": True})
    if not rendered:
        raise RuntimeError("all clip render attempts failed; see diagnostics.jsonl")
    output = destination / ("preview.mp4" if mode == "preview" else "highlights.mp4")
    concat_file = intermediates / "concat.txt"
    concat_file.write_text("".join(f"file '{_concat_path(path)}'\n" for path in rendered), encoding="utf-8")
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
               "-i", str(concat_file), "-c", "copy", str(output)]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except (subprocess.CalledProcessError, OSError) as exc:
        _record(diagnostics, {"stage": "renderer_concat", "timestamp": None, "reason": str(exc), "recovered": False})
        raise RuntimeError(f"could not concatenate clips: {getattr(exc, 'stderr', None) or exc}") from exc
    return output


def _fraction(value: str) -> float:
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def _concat_path(path: Path) -> str:
    """Escape a local path for FFmpeg concat demuxer syntax."""
    return str(path.resolve()).replace("\\", "/").replace("'", "'\\''")


def _record(sink, entry: dict) -> None:
    if sink is not None:
        sink(entry)
