import os
import tempfile
import unittest
from pathlib import Path

from agent.bee_adapter import BeeDataError, load_bee_export
from agent.ring_adapter import RingConfigurationError, fetch_ring_json, runtime_status as ring_status


class DeviceAdapterTests(unittest.TestCase):
    def test_ring_fails_closed_without_token(self):
        old = os.environ.pop("RING_ACCESS_TOKEN", None)
        try:
            with self.assertRaises(RingConfigurationError):
                fetch_ring_json("/v1/devices", base_url="https://example.test")
        finally:
            if old is not None:
                os.environ["RING_ACCESS_TOKEN"] = old

    def test_ring_status_does_not_claim_device_evidence(self):
        value = ring_status(token="redacted", base_url="https://example.test")
        self.assertTrue(value["runtime_configured"])
        self.assertFalse(value["device_or_simulator_evidence"])

    def test_bee_requires_owner_export(self):
        with self.assertRaises(BeeDataError):
            load_bee_export("missing-bee-export.json")

    def test_bee_loads_json_object(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bee.json"
            path.write_text('{"recorded_at":"2026-09-14T00:00:00Z","events":[]}', encoding="utf-8")
            self.assertEqual(load_bee_export(path)["events"], [])


if __name__ == "__main__":
    unittest.main()
