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

    def test_plantnet_gallery_card_uses_only_top_candidate(self):
        payload = {
            "results": [
                {
                    "score": 0.88,
                    "species": {
                        "scientificNameWithoutAuthor": "Hibiscus rosa-sinensis",
                        "commonNames": ["朱槿", "Chinese hibiscus"],
                    },
                },
                {
                    "score": 0.44,
                    "species": {
                        "scientificNameWithoutAuthor": "Hibiscus mutabilis",
                        "commonNames": ["木芙蓉", "Confederate rose"],
                    },
                },
            ]
        }

        plant = app_main.parse_plantnet_result(payload)

        self.assertEqual(plant["zh_name"], "朱槿")
        self.assertEqual(plant["alternatives"][0]["zh_name"], "木芙蓉")
        self.assertFalse(hasattr(app_main, "plant_candidates_for_gallery"))

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

    def test_legacy_snapshot_cache_cleanup_removes_local_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cache_dir = app_main.LOCAL_CACHE_DIR
            app_main.LOCAL_CACHE_DIR = Path(temp_dir)
            legacy_path = app_main.LOCAL_CACHE_DIR / "local_snapshot_queue.json"
            legacy_path.write_text("[]", encoding="utf-8")
            try:
                app_main.clear_legacy_snapshot_cache()
            finally:
                app_main.LOCAL_CACHE_DIR = original_cache_dir

            self.assertFalse(legacy_path.exists())

    def test_worker_404_error_points_to_bad_worker_url(self):
        message = app_main.worker_error_message(404, "error code: 1042")

        self.assertIn("辨識服務尚未部署", message)
        self.assertIn("Worker", message)

    def test_plantnet_400_or_404_asks_for_a_plant_photo(self):
        for status_code in (400, 404):
            message = app_main.worker_error_message(status_code, '{"message":"Species not found"}')

            self.assertIn("沒有辨識到植物", message)
            self.assertNotIn("辨識服務尚未部署", message)

    def test_auth_error_points_to_worker_secret(self):
        message = app_main.worker_error_message(403, '{"message":"Forbidden"}')

        self.assertIn("PLANTNET_API_KEY", message)
        self.assertNotIn("Forbidden", message)

    def test_method_error_asks_for_refresh_without_raw_payload(self):
        message = app_main.worker_error_message(405, '{"error":"Method not allowed"}')

        self.assertIn("重新整理", message)
        self.assertNotIn("Method not allowed", message)

    def test_expired_app_error_asks_for_refresh(self):
        message = app_main.worker_error_message(426, '{"error":"App version expired"}')

        self.assertIn("版本過舊", message)
        self.assertIn("重新整理", message)

    def test_recognition_service_error_is_not_retryable_by_default(self):
        error = app_main.RecognitionServiceError("bad plant photo")

        self.assertFalse(error.retryable)


if __name__ == "__main__":
    unittest.main()
