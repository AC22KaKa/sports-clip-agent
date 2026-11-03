"""Soccer geometry and physics event detector interface."""

from typing import Iterable

from cv.tracker import Track
from index.event_index import Event


def infer_soccer_events(tracks_by_frame: Iterable[tuple[int, list[Track]]]) -> list[Event]:
    """Infer soccer events from ball, player, and goal detections."""
    raise NotImplementedError("soccer geometry event rules are an interface only")
