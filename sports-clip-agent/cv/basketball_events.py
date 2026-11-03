"""Basketball event detector interface for trajectory-based rules."""

from dataclasses import dataclass
from typing import Iterable

from cv.tracker import Track
from index.event_index import Event


@dataclass(frozen=True, slots=True)
class Hoop:
    """Detected hoop center and approximate horizontal scoring line."""
    x: float
    y: float
    width: float


def infer_basketball_events(tracks_by_frame: Iterable[tuple[int, list[Track]]],
                            hoops_by_frame: Iterable[tuple[int, list[Hoop]]]) -> list[Event]:
    """Infer made shots, steals, blocks, passes, and rebounds from tracks."""
    raise NotImplementedError("basketball trajectory event rules are an interface only")
