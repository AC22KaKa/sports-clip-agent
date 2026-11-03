"""Possession and participation-window inference interfaces."""

from dataclasses import dataclass
from typing import Iterable

from cv.tracker import Track


@dataclass(frozen=True, slots=True)
class PossessionWindow:
    """Half-open frame interval attributed to a player track."""
    player_id: int
    start_frame: int
    end_frame: int
    confidence: float


def infer_basketball_possession(tracks_by_frame: Iterable[tuple[int, list[Track]]]) -> list[PossessionWindow]:
    """Infer basketball ball-handler windows and pass-defined boundaries."""
    raise NotImplementedError("basketball possession inference is an interface only")


def infer_soccer_participation(tracks_by_frame: Iterable[tuple[int, list[Track]]],
                               max_ball_distance: float, min_duration_frames: int) -> list[PossessionWindow]:
    """Infer soccer participation windows; this does not promise every touch."""
    raise NotImplementedError("soccer participation inference is an interface only")
