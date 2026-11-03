"""Multi-object tracking interfaces with reusable baseline parameters."""

from dataclasses import dataclass
from typing import Protocol

from cv.detector import Detection


@dataclass(frozen=True, slots=True)
class Track:
    """Tracked object and stable local track identifier."""
    track_id: int
    detection: Detection


class Tracker(Protocol):
    """Backend contract for ByteTrack or BoT-SORT adapters."""
    def update(self, detections: list[Detection], frame_index: int) -> list[Track]:
        """Associate detections with tracks for one frame."""
        ...


def create_tracker(backend: str = "bytetrack", track_buffer: int = 180,
                   track_low_thresh: float = 0.1, conf: float = 0.15) -> Tracker:
    """Construct the configured tracker when its optional dependency exists."""
    raise NotImplementedError(f"{backend} tracking is an interface only (buffer={track_buffer}, low={track_low_thresh}, conf={conf})")
