"""
Unit test for youtube_publish.py:
1. Validates UTC conversion math from IST peak hours (8:00 -> 02:30 UTC, 13:00 -> 07:30 UTC, 18:00 -> 12:30 UTC).
2. Validates SEO metadata generation (COPPA madeForKids, tags count, char limits).
3. Validates request body generation has status.selfDeclaredMadeForKids = True.
4. Validates dry-run execution against an actual video in assets/.
"""

import unittest
from datetime import datetime, timezone
import os
from youtube_publish import (
    ist_to_utc,
    next_peak_times_utc,
    build_metadata,
    upload_video_to_youtube,
    PEAK_HOURS_IST
)


class TestYouTubePublish(unittest.TestCase):

    def test_ist_to_utc_offset_math(self):
        """
        Verify IST to UTC math:
        IST is UTC+5:30.
        8:00 IST  -> 2:30 UTC
        13:00 IST -> 7:30 UTC
        18:00 IST -> 12:30 UTC
        """
        year, month, day = 2026, 9, 5
        
        # Test 8:00 IST
        utc_8 = ist_to_utc(year, month, day, 8, 0)
        self.assertEqual(utc_8.hour, 2)
        self.assertEqual(utc_8.minute, 30)
        self.assertEqual(utc_8.strftime("%H:%M UTC"), "02:30 UTC")
        
        # Test 13:00 IST
        utc_13 = ist_to_utc(year, month, day, 13, 0)
        self.assertEqual(utc_13.hour, 7)
        self.assertEqual(utc_13.minute, 30)
        self.assertEqual(utc_13.strftime("%H:%M UTC"), "07:30 UTC")
        
        # Test 18:00 IST
        utc_18 = ist_to_utc(year, month, day, 18, 0)
        self.assertEqual(utc_18.hour, 12)
        self.assertEqual(utc_18.minute, 30)
        self.assertEqual(utc_18.strftime("%H:%M UTC"), "12:30 UTC")

    def test_next_peak_times_utc(self):
        fixed_now = datetime(2026, 9, 4, 12, 0, 0, tzinfo=timezone.utc)
        slots = next_peak_times_utc(3, start_from=fixed_now)
        self.assertEqual(len(slots), 3)
        # All slots must be valid ISO UTC strings ending in 'Z'
        for s in slots:
            self.assertTrue(s.endswith("Z"))
            self.assertTrue("T02:30:00Z" in s or "T07:30:00Z" in s or "T12:30:00Z" in s)

    def test_build_metadata_coppa_and_limits(self):
        meta = build_metadata(
            video_type="story",
            title="The Magical Elephant",
            topic="An elephant who helps animals in the jungle",
            keywords=["elephant story", "jungle animals"]
        )
        self.assertTrue(meta["selfDeclaredMadeForKids"])
        self.assertTrue(len(meta["title"]) <= 100)
        self.assertTrue(len(meta["description"]) <= 5000)
        self.assertTrue(len(meta["tags"]) <= 30)
        self.assertIn("hindi kahani", [t.lower() for t in meta["tags"]])

    def test_dry_run_upload_validation(self):
        # Locate an existing video file in assets
        test_video = "assets/FINAL_MASTERPIECE.mp4"
        if not os.path.exists(test_video):
            test_video = "assets/conformed_scene_1.mp4"
            
        self.assertTrue(os.path.exists(test_video), f"Test video {test_video} should exist")
        
        res = upload_video_to_youtube(
            video_path=test_video,
            title="The Legend of the Golden Lotus",
            topic="A tale of magic and courage",
            video_type="story",
            publish_at="2026-09-05T02:30:00Z",
            dry_run=True
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["selfDeclaredMadeForKids"])
        self.assertEqual(res["publish_at"], "2026-09-05T02:30:00Z")


if __name__ == "__main__":
    unittest.main(verbosity=2)
