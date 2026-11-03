"""Detector interface for pluggable YOLO, RF-DETR, or WASB backends."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Detection:
    """One object detection in pixel coordinates."""
    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]


class Detector(Protocol):
    """Backend contract for frame-level object detection."""
    def detect(self, frame) -> list[Detection]:
        """Detect ball, players, hoops, goals, or other configured classes."""
        ...


def load_detector(model_path: str | Path, backend: str = "yolo") -> Detector:
    """Create a detector backend after a concrete model adapter is installed."""
    raise NotImplementedError(f"detector backend {backend!r} is an interface only; model_path={model_path}")
