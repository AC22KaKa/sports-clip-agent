"""Load, validate, filter, and merge frame-based sports events."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Event:
    """One detected event with a zero-based, half-open frame interval."""

    type: str
    start_frame: int
    end_frame: int
    confidence: float
    player_id: str | int | None = None
    source_line: int | None = None

    @classmethod
    def from_mapping(cls, value: object, source_line: int | None = None) -> "Event":
        """Validate and construct an event from a decoded JSON object."""
        if not isinstance(value, dict):
            raise ValueError("event must be a JSON object")
        event_type = value.get("type")
        start, end, confidence = value.get("start_frame"), value.get("end_frame"), value.get("confidence")
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("type must be a non-empty string")
        if isinstance(start, bool) or not isinstance(start, int) or start < 0:
            raise ValueError("start_frame must be a non-negative integer")
        if isinstance(end, bool) or not isinstance(end, int) or end <= start:
            raise ValueError("end_frame must be an integer greater than start_frame")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("confidence must be a number between 0 and 1")
        player_id = value.get("player_id")
        if player_id is not None and not isinstance(player_id, (str, int)):
            raise ValueError("player_id must be a string, integer, or null")
        return cls(event_type.strip().upper(), start, end, float(confidence), player_id, source_line)


class EventIndex:
    """In-memory index over valid events loaded from a JSONL file."""

    def __init__(self, events: Iterable[Event]):
        self.events = tuple(sorted(events, key=lambda item: (item.start_frame, item.end_frame, item.type)))

    @classmethod
    def from_jsonl(cls, path: str | Path, diagnostics=None) -> "EventIndex":
        """Load valid JSONL rows, logging malformed rows and continuing."""
        loaded: list[Event] = []
        source = Path(path)
        try:
            lines = source.open("r", encoding="utf-8")
        except OSError as exc:
            _record(diagnostics, {"stage": "event_index", "timestamp": None, "reason": str(exc), "recovered": False})
            raise
        with lines:
            for line_number, raw in enumerate(lines, 1):
                if not raw.strip():
                    continue
                try:
                    loaded.append(Event.from_mapping(json.loads(raw), line_number))
                except (json.JSONDecodeError, ValueError) as exc:
                    _record(diagnostics, {"stage": "event_index", "timestamp": None, "frame": None, "line": line_number, "reason": str(exc), "recovered": True})
        return cls(loaded)

    def filter(self, types: Iterable[str] | None = None, start_frame: int | None = None, end_frame: int | None = None) -> list[Event]:
        """Return events matching types and overlapping a half-open frame window."""
        allowed = {event_type.upper() for event_type in types} if types is not None else None
        return [event for event in self.events
                if (allowed is None or event.type in allowed)
                and (start_frame is None or event.end_frame > start_frame)
                and (end_frame is None or event.start_frame < end_frame)]

    @staticmethod
    def merge_windows(windows: Iterable[tuple[int, int]], gap_frames: int = 0) -> list[tuple[int, int]]:
        """Merge overlapping or near-adjacent half-open frame windows."""
        if gap_frames < 0:
            raise ValueError("gap_frames must be non-negative")
        ordered = sorted(windows)
        if not ordered:
            return []
        merged: list[list[int]] = []
        for start, end in ordered:
            if start < 0 or end <= start:
                raise ValueError("windows must be non-negative, non-empty intervals")
            if merged and start <= merged[-1][1] + gap_frames:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return [(start, end) for start, end in merged]


def _record(sink, entry: dict) -> None:
    if sink is None:
        logger.warning("recoverable error: %s", entry)
    elif callable(sink):
        sink(entry)
    else:
        sink.write(entry)
