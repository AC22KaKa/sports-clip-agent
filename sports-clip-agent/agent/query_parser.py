"""Parse a small bilingual set of natural-language basketball queries."""

from __future__ import annotations

import re
from dataclasses import dataclass


SCORING_TYPES = frozenset({"SCORE", "MADE_2PT", "MADE_3PT", "MADE_FT", "FREE_THROW_MADE", "TWO_POINT_MADE", "THREE_POINT_MADE"})
KEY_TYPES = SCORING_TYPES | frozenset({"STEAL", "BLOCK"})


@dataclass(frozen=True, slots=True)
class EventQuery:
    """Normalized event selection criteria for the clip planner."""

    event_types: frozenset[str]
    last_minutes: float | None = None
    description: str = ""


def parse_query(text: str) -> EventQuery:
    """Parse supported Chinese or English scoring/key-moment queries."""
    normalized = text.strip().lower()
    if not normalized:
        raise ValueError("query cannot be empty")
    scoring = any(term in normalized for term in ("scoring", "score", "得分", "进球", "命中"))
    key = any(term in normalized for term in ("关键", "key moment", "key moments", "highlight", "精彩"))
    if scoring:
        types = SCORING_TYPES
    elif key:
        types = KEY_TYPES
    else:
        raise ValueError("unsupported query; try 'all scoring plays' or '最后5分钟关键时刻'")
    minutes = None
    match = re.search(r"(?:last|最后|最近)\s*(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|分钟)", normalized)
    if match:
        minutes = float(match.group(1))
        if minutes <= 0:
            raise ValueError("query time window must be greater than zero minutes")
    return EventQuery(frozenset(types), minutes, text)
