"""Tests for robust JSONL event indexing and frame-window handling."""

import json
import unittest
from pathlib import Path

from index.event_index import EventIndex


class EventIndexTests(unittest.TestCase):
    def test_load_skips_invalid_line_and_records_diagnostic(self):
        path = Path(__file__).parent / "fixtures" / "events_with_invalid_line.jsonl"
        diagnostics = []
        index = EventIndex.from_jsonl(path, diagnostics.append)
        self.assertEqual(len(index.events), 1)
        self.assertEqual(diagnostics[0]["line"], 2)
        self.assertTrue(diagnostics[0]["recovered"])

    def test_filter_and_merge_half_open_intervals(self):
        index = EventIndex.from_jsonl(Path(__file__).parent / "fixtures" / "events.jsonl")
        self.assertEqual([event.type for event in index.filter({"MADE_FT"})], ["MADE_FT"])
        self.assertEqual(index.filter({"STEAL"}, start_frame=95), [])
        self.assertEqual(EventIndex.merge_windows([(10, 20), (20, 27), (40, 45)], gap_frames=0), [(10, 27), (40, 45)])

    def test_rejects_invalid_event_interval(self):
        with self.assertRaisesRegex(ValueError, "greater than"):
            from index.event_index import Event
            Event.from_mapping({"type": "SCORE", "start_frame": 4, "end_frame": 4, "confidence": 0.5})


if __name__ == "__main__":
    unittest.main()
