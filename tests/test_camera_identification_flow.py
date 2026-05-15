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
                        "commonNames": ["榕樹", "正榕", "Chinese banyan"],
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
        self.assertEqual(plant["aliases"], ["正榕"])
        self.assertEqual(plant["eng_name"], "Chinese banyan")
        self.assertEqual(plant["confidence"], 64.0)
        self.assertFalse(plant["is_low_confidence"])
        self.assertFalse(plant["needs_confirmation"])
        self.assertEqual(plant["alternatives"][0]["zh_name"], "垂榕")

    def test_plantnet_result_marks_lower_scores_as_low_confidence(self):
        payload = {
            "results": [
                {
                    "score": 0.44,
                    "species": {
                        "scientificNameWithoutAuthor": "Ficus benjamina",
                        "commonNames": ["垂榕", "Weeping fig"],
                    },
                },
            ]
        }

        plant = app_main.parse_plantnet_result(payload)

        self.assertEqual(plant["confidence"], 44.0)
        self.assertTrue(plant["is_low_confidence"])
        self.assertTrue(plant["needs_confirmation"])

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

    def test_camera_zoom_is_clamped_to_supported_preview_range(self):
        self.assertEqual(app_main.clamp_camera_zoom(0.5), 1.0)
        self.assertEqual(app_main.clamp_camera_zoom(1.26), 1.25)
        self.assertEqual(app_main.clamp_camera_zoom(2.5), 2.0)

    def test_camera_preview_metrics_keep_zoom_centered_in_lens(self):
        size, left, top = app_main.camera_preview_metrics(1.5)

        self.assertEqual(size, 630)
        self.assertEqual(left, -163)
        self.assertEqual(top, -163)

    def test_preferred_camera_selection_uses_back_main_then_front(self):
        cameras = [
            {"name": "Back Ultra Wide Camera 0.5x"},
            {"name": "Front Selfie Camera"},
            {"name": "Back Main Camera"},
            {"name": "Back Telephoto Camera 2x"},
        ]

        selected = app_main.select_preferred_cameras(cameras)

        self.assertEqual(selected, [cameras[2], cameras[1]])

    def test_preferred_camera_selection_falls_back_to_first_unknown_camera(self):
        cameras = [{"name": "Mystery Camera A"}, {"name": "Mystery Camera B"}]

        selected = app_main.select_preferred_cameras(cameras)

        self.assertEqual(selected, [cameras[0]])

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

    def test_known_metadata_is_attached_by_scientific_name(self):
        plant = app_main.plant_candidate_from_result(
            {
                "score": 0.91,
                "species": {
                    "scientificNameWithoutAuthor": "Ficus microcarpa",
                    "commonNames": ["榕樹", "Chinese banyan"],
                },
            }
        )

        self.assertEqual(plant["toxicity"]["label"], "無明確毒性資料")
        self.assertEqual(plant["invasive"]["label"], "非外來種")

    def test_unknown_metadata_uses_conservative_pending_labels(self):
        plant = app_main.plant_candidate_from_result(
            {
                "score": 0.91,
                "species": {
                    "scientificNameWithoutAuthor": "Unknown plant",
                    "commonNames": ["未知植物", "Mystery plant"],
                },
            }
        )

        self.assertEqual(plant["toxicity"]["label"], "資料待確認")
        self.assertEqual(plant["invasive"]["label"], "資料待確認")

    def test_perenual_metadata_enriches_top_plant_candidate(self):
        payload = {
            "perenual": {
                "status": "ok",
                "poisonous_to_humans": True,
                "poisonous_to_pets": True,
                "invasive": False,
                "watering": "Average",
                "sunlight": ["full sun"],
                "cycle": "Perennial",
                "description": "Perenual detail text.",
            },
            "results": [
                {
                    "score": 0.8,
                    "species": {
                        "scientificNameWithoutAuthor": "Nerium oleander",
                        "commonNames": ["夾竹桃", "Oleander"],
                    },
                },
            ],
        }

        plant = app_main.parse_plantnet_result(payload)

        self.assertEqual(plant["toxicity"]["label"], "有毒")
        self.assertIn("寵物", plant["toxicity"]["detail"])
        self.assertEqual(plant["invasive"]["label"], "未列為侵略性")
        self.assertEqual(plant["care"]["澆水"], "Average")
        self.assertEqual(plant["metadata_source"], "Perenual")
        self.assertEqual(plant["desc"], "Perenual detail text.")

    def test_card_image_data_url_is_bounded_for_storage(self):
        capture = "data:image/jpeg;base64," + ("a" * 20000)

        image = app_main.card_image_from_capture(capture, max_data_url_length=120)

        self.assertEqual(image["src"], "")
        self.assertEqual(image["label"], "照片過大，未存入圖鑑")


if __name__ == "__main__":
    unittest.main()
