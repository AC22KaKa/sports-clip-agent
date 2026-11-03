"""Tests for bilingual query parsing and clip interval planning."""

import unittest
from pathlib import Path

from agent.clip_planner import plan_clips
from agent.query_parser import KEY_TYPES, SCORING_TYPES, parse_query
from index.event_index import EventIndex


class QueryPlannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = EventIndex.from_jsonl(Path(__file__).parent / "fixtures" / "events.jsonl")

    def test_scoring_aliases_english_and_chinese_time_window(self):
        self.assertEqual(parse_query("all scoring plays").event_types, SCORING_TYPES)
        query = parse_query("最后5分钟关键时刻")
        self.assertEqual(query.last_minutes, 5)
        self.assertEqual(query.event_types, KEY_TYPES)
        self.assertEqual(parse_query("last 2 minutes key moments").last_minutes, 2)

    def test_scoring_excludes_missed_shots_and_padding_clamps_to_video(self):
        clips = plan_clips(self.index, parse_query("all scoring plays"), fps=10, duration_seconds=20)
        self.assertEqual([clip.event_type for clip in clips], ["MADE_2PT", "MADE_FT"])
        self.assertEqual(clips[0].start_frame, 0)
        self.assertEqual(clips[0].end_frame, 65)
        self.assertAlmostEqual(clips[1].start_seconds, 7.5)

    def test_last_minutes_uses_video_end(self):
        clips = plan_clips(self.index, parse_query("last 5 minutes key moments"), fps=10, duration_seconds=20)
        self.assertEqual([clip.event_type for clip in clips], ["MADE_2PT", "STEAL", "MADE_FT", "BLOCK"])

    def test_unsupported_query_is_actionable(self):
        with self.assertRaisesRegex(ValueError, "unsupported query"):
            parse_query("show me something")


if __name__ == "__main__":
    unittest.main()
