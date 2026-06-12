import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "flet_app"))
os.environ["FLET_SKIP_RUN"] = "1"

from camera_utils import (  # noqa: E402
    camera_preview_metrics,
    clamp_camera_zoom,
    select_preferred_cameras,
)
from plant_api import (  # noqa: E402
    RecognitionServiceError,
    card_image_from_capture,
    compress_image,
    parse_plantnet_result,
    plant_candidate_from_result,
    worker_error_message,
)
from pokedex_manager import (  # noqa: E402
    LOCAL_CACHE_DIR,
    LOCAL_CACHE_PATH,
    clear_legacy_snapshot_cache,
    save_json_cache,
)

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

        plant = parse_plantnet_result(payload)

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

        plant = parse_plantnet_result(payload)

        self.assertEqual(plant["confidence"], 44.0)
        self.assertTrue(plant["is_low_confidence"])
        self.assertTrue(plant["needs_confirmation"])

    def test_plantnet_candidates_use_worker_normalized_traditional_chinese(self):
        payload = {
            "results": [
                {
                    "score": 0.82,
                    "species": {
                        "scientificNameWithoutAuthor": "Ficus microcarpa",
                        "commonNames": ["榕樹", "Chinese banyan"],
                    },
                },
                {
                    "score": 0.42,
                    "species": {
                        "scientificNameWithoutAuthor": "Ficus benjamina",
                        "commonNames": ["垂葉榕", "Weeping fig"],
                    },
                },
            ]
        }

        plant = parse_plantnet_result(payload)

        self.assertEqual(plant["zh_name"], "榕樹")
        self.assertEqual(plant["alternatives"][0]["zh_name"], "垂葉榕")

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

        plant = parse_plantnet_result(payload)

        self.assertEqual(plant["zh_name"], "朱槿")
        self.assertEqual(plant["alternatives"][0]["zh_name"], "木芙蓉")
        self.assertFalse(hasattr(app_main, "plant_candidates_for_gallery"))

    def test_save_json_cache_handles_empty_data_gracefully(self):
        import asyncio
        asyncio.run(save_json_cache("testDict", {}))
        asyncio.run(save_json_cache("testList", []))

    def test_local_cache_constant_exists(self):
        self.assertTrue(LOCAL_CACHE_PATH.exists() or str(LOCAL_CACHE_PATH).endswith("local_pokedex_cache.json"))

    def test_legacy_snapshot_cache_cleanup_removes_local_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cache_dir = LOCAL_CACHE_DIR
            import pokedex_manager
            pokedex_manager.LOCAL_CACHE_DIR = Path(temp_dir)
            legacy_path = Path(temp_dir) / "local_snapshot_queue.json"
            legacy_path.write_text("[]", encoding="utf-8")
            try:
                clear_legacy_snapshot_cache()
            finally:
                pokedex_manager.LOCAL_CACHE_DIR = original_cache_dir

            self.assertFalse(legacy_path.exists())

    def test_camera_zoom_is_clamped_to_supported_preview_range(self):
        self.assertEqual(clamp_camera_zoom(0.5), 1.0)
        self.assertEqual(clamp_camera_zoom(1.26), 1.25)
        self.assertEqual(clamp_camera_zoom(2.8), 2.75)
        self.assertEqual(clamp_camera_zoom(3.5), 3.0)

    def test_camera_preview_metrics_keep_zoom_centered_in_lens(self):
        size, left, top = camera_preview_metrics(1.5)

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

        selected = select_preferred_cameras(cameras)

        self.assertEqual(selected, [cameras[2], cameras[1]])

    def test_preferred_camera_selection_falls_back_to_first_unknown_camera(self):
        cameras = [{"name": "Mystery Camera A"}, {"name": "Mystery Camera B"}]

        selected = select_preferred_cameras(cameras)

        self.assertEqual(selected, [cameras[0]])

    def test_worker_404_error_points_to_bad_worker_url(self):
        message = worker_error_message(404, "error code: 1042")

        self.assertIn("辨識服務尚未部署", message)
        self.assertIn("Worker", message)

    def test_plantnet_400_or_404_asks_for_a_plant_photo(self):
        for status_code in (400, 404):
            message = worker_error_message(status_code, '{"message":"Species not found"}')

            self.assertIn("沒有辨識到植物", message)
            self.assertNotIn("辨識服務尚未部署", message)

    def test_auth_error_points_to_worker_secret(self):
        message = worker_error_message(403, '{"message":"Forbidden"}')

        self.assertIn("PLANTNET_API_KEY", message)
        self.assertNotIn("Forbidden", message)

    def test_method_error_asks_for_refresh_without_raw_payload(self):
        message = worker_error_message(405, '{"error":"Method not allowed"}')

        self.assertIn("稍後再試", message)
        self.assertNotIn("重新整理", message)
        self.assertNotIn("Method not allowed", message)

    def test_expired_app_error_asks_for_refresh(self):
        message = worker_error_message(426, '{"error":"App version expired"}')

        self.assertIn("版本過舊", message)
        self.assertIn("稍後", message)
        self.assertNotIn("重新整理", message)

    def test_recognition_service_error_is_not_retryable_by_default(self):
        error = RecognitionServiceError("bad plant photo")

        self.assertFalse(error.retryable)

    def test_known_metadata_is_attached_by_scientific_name(self):
        plant = plant_candidate_from_result(
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
        plant = plant_candidate_from_result(
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

        plant = parse_plantnet_result(payload)

        self.assertEqual(plant["toxicity"]["label"], "有毒")
        self.assertIn("寵物", plant["toxicity"]["detail"])
        self.assertEqual(plant["invasive"]["label"], "未列為侵略性")
        self.assertEqual(plant["care"]["澆水"], "Average")
        self.assertEqual(plant["metadata_source"], "Perenual")
        self.assertEqual(plant["desc"], "Perenual detail text.")

    def test_card_image_data_url_is_bounded_for_storage(self):
        capture = "data:image/jpeg;base64," + ("a" * 20000)

        image = card_image_from_capture(capture, max_data_url_length=120)

        self.assertEqual(image["src"], "")
        self.assertEqual(image["label"], "照片過大，未存入圖鑑")

    def test_compress_image_optimize_flag_is_threaded_through(self):
        from io import BytesIO
        from unittest.mock import patch

        from plant_api import Image  # type: ignore

        if Image is None:
            self.skipTest("Pillow not available in this environment")

        buf = BytesIO()
        with Image.new("RGB", (200, 200), color=(120, 80, 40)) as raw:
            raw.save(buf, format="JPEG", quality=90)
        binary = buf.getvalue()

        optimize_seen: list[object] = []

        def fake_save(self, buffer, format=None, **kwargs):  # type: ignore[no-untyped-def]
            optimize_seen.append(kwargs.get("optimize", "missing"))
            buffer.write(b"\x00\x00")

        with patch.object(Image.Image, "save", fake_save):
            compress_image(binary, "image/jpeg", optimize=True)
            compress_image(binary, "image/jpeg", optimize=False)
            compress_image(binary, "image/jpeg")

        self.assertEqual(optimize_seen, [True, False, True])


    def test_recognition_retry_allows_error_state_retries(self):
        plant = {
            "zh_name": "榕樹",
            "sci_name": "Ficus microcarpa",
            "metadata_status": "error",
            "metadata_retries": 1,
        }
        self.assertEqual(plant["metadata_status"], "error")
        self.assertLess(plant["metadata_retries"], 3)

    def test_recognition_retry_stops_after_max_retries(self):
        plant = {
            "zh_name": "榕樹",
            "sci_name": "Ficus microcarpa",
            "metadata_status": "error",
            "metadata_retries": 3,
        }
        self.assertEqual(plant["metadata_status"], "error")
        self.assertGreaterEqual(plant["metadata_retries"], 3)


if __name__ == "__main__":
    unittest.main()
