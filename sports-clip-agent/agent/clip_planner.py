"""Turn a normalized query and event index into a clip manifest."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from agent.query_parser import EventQuery
from index.event_index import EventIndex


@dataclass(frozen=True, slots=True)
class ClipSegment:
    """Planned source-video interval and the event that selected it."""

    event_type: str
    event_start_frame: int
    event_end_frame: int
    start_frame: int
    end_frame: int
    start_seconds: float
    end_seconds: float
    confidence: float
    player_id: str | int | None = None

    def to_dict(self) -> dict:
        """Return a JSON-serializable manifest entry."""
        return asdict(self)


def plan_clips(index: EventIndex, query: EventQuery, fps: float, duration_seconds: float,
               padding_seconds: float = 3.0) -> list[ClipSegment]:
    """Select events and expand them by context padding within video bounds."""
    if fps <= 0 or duration_seconds <= 0 or padding_seconds < 0:
        raise ValueError("fps and duration must be positive; padding must be non-negative")
    video_end = int(duration_seconds * fps)
    window_start = 0 if query.last_minutes is None else max(0, video_end - int(query.last_minutes * 60 * fps))
    selected = index.filter(query.event_types, start_frame=window_start)
    pad = int(round(padding_seconds * fps))
    result = []
    for event in selected:
        start = max(0, event.start_frame - pad)
        end = min(video_end, event.end_frame + pad)
        if end <= start:
            continue
        result.append(ClipSegment(event.type, event.start_frame, event.end_frame, start, end,
                                  start / fps, end / fps, event.confidence, event.player_id))
    return result
