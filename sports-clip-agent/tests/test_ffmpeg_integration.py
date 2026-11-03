"""Optional short-video integration test; requires FFmpeg and ffprobe."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent.clip_planner import plan_clips
from agent.query_parser import parse_query
from index.event_index import EventIndex
from render.ffmpeg_renderer import probe_video, render_clips


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is not installed")
class FFmpegIntegrationTests(unittest.TestCase):
    def test_preview_and_final_render(self):
        fixture = Path(__file__).parent / "fixtures" / "events.jsonl"
        index = EventIndex.from_jsonl(fixture)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            root = Path(directory)
            video = root / "source.mp4"
            subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10:duration=20",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video)], check=True)
            fps, duration = probe_video(video)
            self.assertAlmostEqual(fps, 10, delta=0.1)
            clips = plan_clips(index, parse_query("all scoring plays"), fps, duration)
            preview = render_clips(video, clips, root / "preview_out", "preview")
            final = render_clips(video, clips, root / "render_out", "render")
            self.assertTrue(preview.is_file())
            self.assertTrue(final.is_file())
            self.assertGreater(preview.stat().st_size, 0)
            self.assertGreater(final.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
