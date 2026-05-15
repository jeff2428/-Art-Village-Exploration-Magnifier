from pathlib import Path
import os
import tempfile
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "flet_app"))
os.environ["FLET_SKIP_RUN"] = "1"

import main as app_main  # noqa: E402


class CameraIdentificationFlowTests(unittest.TestCase):
    def test_plantnet_result_tracks_confidence_and_alternatives(self):
        payload = {
            "results": [
                {
                    "score": 0.64,
                    "species": {
                        "scientificNameWithoutAuthor": "Ficus microcarpa",
                        "commonNames": ["榕樹", "Chinese banyan"],
                    },
                },
                {
                    "score": 0.22,
                    "species": {
                        "scientificNameWithoutAuthor": "Ficus benjamina",
                        "commonNames": ["垂榕", "Weeping fig"],
                    },
                },
            ]
        }

        plant = app_main.parse_plantnet_result(payload)

        self.assertIsNotNone(plant)
        self.assertEqual(plant["zh_name"], "榕樹")
        self.assertEqual(plant["confidence"], 64.0)
        self.assertTrue(plant["is_low_confidence"])
        self.assertTrue(plant["needs_confirmation"])
        self.assertEqual(plant["alternatives"][0]["zh_name"], "垂榕")

    def test_snapshot_cache_round_trip_for_offline_retry(self):
        capture = b"fake-jpeg-bytes"

        snapshot = app_main.make_snapshot(capture)
        restored = app_main.snapshot_to_capture(snapshot)
        binary, mime = app_main.capture_to_bytes(restored)

        self.assertEqual(binary, capture)
        self.assertEqual(mime, "image/jpeg")

    def test_empty_local_cache_does_not_write_on_startup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            empty_dict = Path(temp_dir) / "empty_dict.json"
            empty_list = Path(temp_dir) / "empty_list.json"

            app_main.save_json_cache("testDict", empty_dict, {})
            app_main.save_json_cache("testList", empty_list, [])

            self.assertFalse(empty_dict.exists())
            self.assertFalse(empty_list.exists())

    def test_local_cache_lives_outside_flet_app_watch_directory(self):
        self.assertNotEqual(app_main.LOCAL_CACHE_PATH.parent, ROOT / "flet_app")
        self.assertNotEqual(app_main.LOCAL_SNAPSHOT_QUEUE_PATH.parent, ROOT / "flet_app")

    def test_worker_404_error_points_to_bad_worker_url(self):
        message = app_main.worker_error_message(404, "<!DOCTYPE html><html>not found</html>")

        self.assertIn("辨識服務網址無效", message)
        self.assertIn("404", message)


if __name__ == "__main__":
    unittest.main()
