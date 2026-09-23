"""Verify that the local Alexa+ video generator renders real MCP case output."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "make-alexa-plus-video.py"


def load_video_module():
    spec = importlib.util.spec_from_file_location("rewardradar_alexa_video", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AlexaVideoScriptTests(unittest.TestCase):
    def test_case_transcript_uses_a_real_resumable_case(self):
        module = load_video_module()
        planned, reviewed = module.case_transcript()

        self.assertEqual(planned["casefile"]["state"], "open")
        self.assertEqual(len(planned["casefile"]["fixture_digest_sha256"]), 64)
        self.assertTrue(reviewed["case_found"])
        self.assertEqual(reviewed["focus"], "comparison")
        self.assertIn("alternatives", reviewed["evidence_card"])
        self.assertFalse(reviewed["safety"]["payout_guaranteed"])


if __name__ == "__main__":
    unittest.main()
