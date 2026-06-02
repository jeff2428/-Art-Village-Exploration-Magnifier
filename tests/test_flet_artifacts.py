import importlib.util
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_loader_patcher():
    spec = importlib.util.spec_from_file_location(
        "patch_flet_loader",
        ROOT / "scripts" / "patch_flet_loader.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_app_package_patcher():
    spec = importlib.util.spec_from_file_location(
        "patch_flet_app_package",
        ROOT / "scripts" / "patch_flet_app_package.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FletArtifactsTests(unittest.TestCase):
    def test_streamlit_frontend_is_removed(self):
        self.assertFalse((ROOT / "app.py").exists())
        self.assertFalse((ROOT / "style.css").exists())
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertNotIn("streamlit", requirements.lower())

    def test_worker_uses_secret_env_and_restricts_github_io_origins(self):
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")
        wrangler = (ROOT / "worker" / "wrangler.toml").read_text(encoding="utf-8")

        self.assertIn("env.PLANTNET_API_KEY", worker)
        self.assertIn("PERENUAL_SPECIES_LIST_URL", worker)
        self.assertIn("PERENUAL_DETAILS_URL", worker)
        self.assertIn("env.PERENUAL_API_KEY", worker)
        self.assertIn("fetchPerenualMetadataCached(scientificName, env)", worker)
        self.assertIn('requestUrl.pathname === "/metadata"', worker)
        self.assertIn('status: "pending"', worker)
        self.assertIn("plantnet_ms", worker)
        self.assertIn("perenual_ms", worker)
        self.assertIn("total_ms", worker)
        self.assertIn("Server-Timing", worker)
        self.assertIn("caches.default.match", worker)
        self.assertIn("caches.default.put", worker)
        self.assertNotIn("plantNetPayload.perenual = await fetchPerenualMetadata", worker)
        self.assertIn("poisonous_to_humans", worker)
        self.assertIn("poisonous_to_pets", worker)
        self.assertNotIn("2b1004", worker)
        self.assertIn('"api-key": env.PLANTNET_API_KEY', worker)
        self.assertNotIn("Authorization", worker)
        self.assertIn("github.io", worker)
        self.assertIn("pages.dev", worker)
        self.assertIn("ALLOWED_ORIGIN", worker)
        self.assertIn("Access-Control-Allow-Origin", worker)
        self.assertIn("isFileLike", worker)
        self.assertIn("Worker proxy failed", worker)
        self.assertIn("URLSearchParams", worker)
        self.assertIn('incomingForm.get("organs")', worker)
        self.assertIn("allowedOrgans.has(organ)", worker)
        self.assertIn('plantNetForm.append("organs", organ)', worker)
        self.assertNotIn('"no-reject": "true"', worker)
        self.assertIn('request.method === "GET"', worker)
        self.assertIn("App version expired", worker)
        self.assertIn("status: 426", worker)
        self.assertIn('name = "art-village-magnifier"', wrangler)
        self.assertIn('main = "index.js"', wrangler)
        self.assertIn("ALLOW_PAGES_DOMAINS", wrangler)
        self.assertIn("MAX_UPLOAD_BYTES", wrangler)

    def test_worker_enforces_upload_size_and_image_mime(self):
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")

        self.assertIn("MAX_UPLOAD_BYTES", worker)
        self.assertIn("DEFAULT_MAX_UPLOAD_BYTES", worker)
        self.assertIn("ALLOWED_IMAGE_MIME", worker)
        self.assertIn("image/jpeg", worker)
        self.assertIn("image/png", worker)
        self.assertIn("image/webp", worker)
        self.assertIn("readMaxUploadBytes(env)", worker)
        self.assertIn("Content-Length", worker)
        self.assertIn("Upload too large", worker)
        self.assertIn("Unsupported image type", worker)

    def test_worker_cors_defaults_to_off_for_pages_domains(self):
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")

        self.assertIn("isPagesDomainAllowed", worker)
        self.assertIn('ALLOW_PAGES_DOMAINS', worker)
        # 預設不再 fallback 寫死 "https://pages.dev"
        self.assertNotIn('return "https://pages.dev";', worker)

    def test_flet_app_has_magnifier_handle_callbacks(self):
        handle = (ROOT / "flet_app" / "magnifier_handle.py").read_text(encoding="utf-8")

        self.assertIn("class MagnifierHandle", handle)
        self.assertIn("on_switch", handle)
        self.assertIn("on_capture", handle)
        self.assertIn("on_room_in", handle)
        self.assertIn("on_room_out", handle)
        self.assertIn("room_in_enabled", handle)
        self.assertIn("room_out_enabled", handle)
        self.assertIn("Room in", handle)
        self.assertIn("Room out", handle)
        self.assertIn("show_label=False", handle)
        self.assertIn("size=32", handle)
        self.assertIn("width=160", handle)
        self.assertIn("left=118", handle)
        self.assertIn("top=44", handle)
        self.assertIn("top=148", handle)
        self.assertIn("capture_enabled", handle)
        self.assertNotIn("disabled=not capture_enabled", handle)
        self.assertIn("RadialGradient", handle)
        self.assertIn("tooltip=label", handle)
        self.assertNotIn("ft.border_radius.only", handle)

    def test_flet_main_uses_worker_and_camera(self):
        main = (ROOT / "flet_app" / "main.py").read_text(encoding="utf-8")
        camera_utils = (ROOT / "flet_app" / "camera_utils.py").read_text(encoding="utf-8")
        plant_api = (ROOT / "flet_app" / "plant_api.py").read_text(encoding="utf-8")
        pokedex_manager = (ROOT / "flet_app" / "pokedex_manager.py").read_text(encoding="utf-8")

        self.assertIn("flet_camera", main)
        self.assertIn("run_app", main)
        self.assertIn("探險放大鏡啟動中", main)
        self.assertIn("探險放大鏡載入失敗", main)
        self.assertIn("重新啟動相機", main)
        self.assertIn("camera_initializing", main)
        self.assertIn("asyncio.wait_for(state.camera.get_available_cameras(", main)
        self.assertIn("asyncio.wait_for(", main)
        self.assertIn("create_background_task(initialize_camera()", main)
        self.assertIn("select_preferred_cameras", main)
        self.assertIn("on_room_in=room_in", main)
        self.assertIn("on_room_out=room_out", main)
        self.assertNotIn("on_scale_start=on_pinch_start", main)
        self.assertNotIn("on_scale_update=on_pinch_update", main)
        self.assertIn("MIN_CAMERA_ZOOM", main)
        self.assertIn("MAX_CAMERA_ZOOM", main)
        self.assertIn("clamp_camera_zoom", main)
        self.assertNotIn("(selected_camera_index + 1) % len(cameras)", main)
        self.assertIn("create_background_task(save_cached_pokedex", main)
        self.assertIn("mark_load_timing", main)
        self.assertIn("art-village:shell-ready", main)
        self.assertIn("art-village:camera-ready", main)
        self.assertIn("camera_ready", main)
        self.assertIn("capture_enabled=state.camera_ready", main)
        self.assertIn("camera_viewport", main)
        self.assertIn("LENS_VIEWPORT_SIZE", main)
        self.assertIn("CAMERA_PREVIEW_SIZE = 420", camera_utils)
        self.assertIn("CAMERA_PREVIEW_OFFSET = -58", camera_utils)
        self.assertIn("POKEDEX_STORAGE_KEY", pokedex_manager)
        self.assertIn("LOCAL_CACHE_DIR", pokedex_manager)
        self.assertIn("tempfile.gettempdir()", pokedex_manager)
        self.assertIn("LOCAL_CACHE_PATH", pokedex_manager)
        self.assertIn("localStorage", pokedex_manager)
        self.assertIn("LOW_CONFIDENCE_THRESHOLD", plant_api)
        self.assertIn("LOW_CONFIDENCE_THRESHOLD = 50.0", plant_api)
        self.assertIn("PLANT_ORGAN_OPTIONS", main)
        self.assertIn("MAX_CARD_IMAGE_DATA_URL_LENGTH", plant_api)
        self.assertIn("PLANT_METADATA", plant_api)
        self.assertIn("UNKNOWN_METADATA", main)
        self.assertIn("metadata_for_scientific_name", main)
        self.assertIn("metadata_from_perenual", main)
        self.assertIn("metadata_url_for_scientific_name", plant_api)
        self.assertIn("get_metadata_from_worker", main)
        self.assertIn("refresh_plant_metadata", main)
        self.assertIn('plant.get("metadata_status") == "pending"', main)
        self.assertIn("worker_timing", main)
        self.assertIn("art-village:identify-start", main)
        self.assertIn("art-village:identify-primary-ready", main)
        self.assertIn("payload.get(\"perenual\")", plant_api)
        self.assertIn("Perenual 植物資料", main)
        self.assertIn("資料來源", main)
        self.assertIn("common_names_by_script", plant_api)
        self.assertIn("card_image_from_capture", main)
        self.assertIn("organ_mode = ft.SegmentedButton", main)
        self.assertIn('selected=["auto"]', main)
        self.assertIn("PLANT_ORGAN_ICONS", main)
        self.assertIn("ft.Segment", main)
        self.assertIn("selected_organ_value", main)
        self.assertIn("organ_selector", main)
        self.assertIn("scrollable=True", main)
        self.assertIn("dialog_content_height", main)
        self.assertIn("scroll=ft.ScrollMode.AUTO", main)
        self.assertIn("拍攝部位", main)
        self.assertIn("captured_image", main)
        self.assertIn("ft.BoxFit.COVER", main)
        self.assertNotIn("ft.ImageFit", main)
        self.assertIn("ft.Padding.symmetric", main)
        self.assertNotIn("ft.padding.symmetric", main)
        self.assertIn("aliases", main)
        self.assertIn("毒性", main)
        self.assertIn("外來種", main)
        self.assertIn("尚無拍攝照片", main)
        self.assertIn("post_image_to_worker(image_data, selected_organ)", main)
        self.assertIn("show_recognition_loading_card()", main)
        self.assertIn("close_recognition_loading_card(update_page=False)", main)
        self.assertIn("辨識中", main)
        self.assertIn('show_plant_card(plant["zh_name"], plant)', main)
        self.assertIn("alternatives", main)
        self.assertIn("建議確認", main)
        self.assertIn("clear_legacy_snapshot_cache", main)
        self.assertNotIn("make_snapshot", main)
        self.assertNotIn("snapshot_to_capture", main)
        self.assertNotIn("retry_pending_snapshots", main)
        self.assertNotIn("離線暫存快照", main)
        self.assertNotIn("重送暫存快照", main)
        self.assertIn("ProgressRing", main)
        self.assertNotIn("藝素村手繪探險圖鑑", main)
        self.assertNotIn('section_label("🔍", "探險鏡頭")', main)
        self.assertIn('selected_mode = {"value": "plant"}', main)
        self.assertNotIn("ft.RadioGroup", main)
        self.assertIn("WORKER_URL", plant_api)
        self.assertIn("尚未設定 Cloudflare Pages 的 WORKER_URL", plant_api)
        self.assertIn("worker_error_message", plant_api)
        self.assertIn("Object.fromEntries", plant_api)
        self.assertIn("mark_explorer_ready", main)
        self.assertIn("__artVillageReady", main)
        self.assertIn("辨識服務尚未部署", plant_api)
        self.assertIn("PLANTNET_API_KEY", plant_api)
        self.assertIn("正在初始化相機", main)
        self.assertIn("相機元件準備中，正在重試", main)
        self.assertIn("TimeoutException", main)
        self.assertIn("requests.post", plant_api)
        self.assertIn("take_picture", main)
        self.assertIn("set_description", main)
        self.assertIn("GridView", main)
        self.assertIn("ft.run(main)", main)
        self.assertIn("FLET_SKIP_RUN", main)
        self.assertNotIn('__name__ == "__main__"', main)
        self.assertNotIn("text=f", main)
        self.assertIn("認識動物", main)
        self.assertIn("show_animal_card", main)
        self.assertIn("page.show_dialog", main)
        self.assertIn("content_area.content = get_animals_view()", main)
        self.assertIn("build_mode_selector", main)
        self.assertIn("ft.TextButton", main)
        self.assertIn("selected_mode[\"value\"] == \"animal\"", main)
        self.assertIn('page.launch_url("./admin/animals.html")', main)
        self.assertIn("ft.Margin.only", main)
        self.assertNotIn("ft.margin.only", main)
        self.assertIn("WARNING_AMBER_OUTLINED", main)
        self.assertNotIn("WARNING_AMBIGUOUS", main)
        self.assertIn("confirm_clear_gallery", main)
        self.assertIn("clear_gallery", main)
        self.assertIn("confirm_delete_gallery_item", main)
        self.assertIn("delete_gallery_item", main)
        self.assertIn("on_long_press=lambda _event, item_name=name", main)
        self.assertIn("清除圖鑑內容", main)
        self.assertIn("DELETE_SWEEP_OUTLINED", main)
        self.assertIn("welcome_screen", main)
        self.assertIn("start_exploration", main)
        self.assertIn("report_performance", main)
        self.assertIn("welcome_screen.visible = False", main)

    def test_lightweight_web_prototype_exists_for_framework_comparison(self):
        prototype = (ROOT / "prototype" / "index.html").read_text(encoding="utf-8")

        self.assertIn("navigator.mediaDevices.getUserMedia", prototype)
        self.assertIn("FormData", prototype)
        self.assertIn("performance.mark(\"prototype:loader-start\")", prototype)
        self.assertIn("prototype:identify-primary-ready", prototype)
        self.assertIn("Worker timing", prototype)

    def test_cloudflare_pages_builds_and_patches_loader(self):
        build = (ROOT / "build.sh").read_text(encoding="utf-8")
        dev = (ROOT / "scripts" / "dev.ps1").read_text(encoding="utf-8")
        install_dev = (ROOT / "scripts" / "install-dev.ps1").read_text(encoding="utf-8")
        patcher = (ROOT / "scripts" / "patch_flet_loader.py").read_text(encoding="utf-8")
        wrangler = (ROOT / "wrangler.toml").read_text(encoding="utf-8")

        self.assertFalse((ROOT / ".github" / "workflows" / "deploy.yml").exists())
        self.assertIn("flet build web", build)
        self.assertIn("FLET_CLI_NO_RICH_OUTPUT", build)
        self.assertIn('python -m pip install "flet-cli==0.85.1"', build)
        self.assertNotIn("flet-cli", (ROOT / "flet_app" / "requirements.txt").read_text(encoding="utf-8"))
        self.assertNotIn("flet-cli", (ROOT / "flet_app" / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn("--yes", build)
        self.assertIn("--route-url-strategy hash", build)
        self.assertIn("--web-renderer auto", build)
        self.assertIn("WORKER_URL", build)
        self.assertIn("PRE_BUILD_NOTES.md", build)
        self.assertIn("patch_flet_loader.py", build)
        self.assertIn("patch_flet_app_package.py", build)
        self.assertIn("FLET_BUILD_ID", build)
        self.assertIn("_headers", build)
        self.assertIn("Cache-Control: no-store", build)
        self.assertIn("/assets/app/app-*.zip", build)
        self.assertIn("max-age=31536000, immutable", build)
        self.assertIn('pages_build_output_dir = "flet_app/build/web"', wrangler)
        self.assertIn("flet_app/build/web/index.html", patcher)
        self.assertIn("探險家載入中", patcher)
        self.assertIn("explorer-fade", patcher)
        self.assertIn("hasFletContent", patcher)
        self.assertIn("art-village:loader-start", patcher)
        self.assertIn("resource_hints", patcher)
        self.assertIn('rel="preload"', patcher)
        self.assertIn("assets/app/{versioned_name}", patcher)
        self.assertIn("pyodide/pyodide.js", patcher)
        self.assertIn("canvaskit/canvaskit.js", patcher)
        self.assertIn("__artVillageReady", patcher)
        self.assertIn("45000", patcher)
        self.assertIn("serviceWorker", patcher)
        self.assertIn("caches.keys", patcher)
        self.assertIn("artVillageBuildId", patcher)
        self.assertIn("shouldRefreshRuntimeCache", patcher)
        self.assertIn("app-{stamp}.zip", patcher)
        self.assertIn("flet-cache-buster", patcher)
        self.assertIn("appPackageUrl", patcher)
        self.assertIn("pyodideUrl", patcher)
        self.assertIn("performance.measure", patcher)
        self.assertIn("loader-duration", patcher)
        self.assertIn("generate_service_worker", patcher)
        self.assertIn("sw.js", patcher)
        self.assertIn("Cross-Origin-Opener-Policy", build)
        self.assertIn("Cross-Origin-Embedder-Policy", build)
        self.assertIn("credentialless", build)
        package_patcher = (ROOT / "scripts" / "patch_flet_app_package.py").read_text(encoding="utf-8")
        self.assertIn("local_python_modules", package_patcher)
        self.assertIn("admin/animals.json", package_patcher)
        self.assertIn("cp -R admin flet_app/build/web/admin", build)
        self.assertIn("flet run -d -w main.py", dev)
        self.assertIn("flet_app/requirements.txt", install_dev)

    def test_build_sh_emits_security_headers(self):
        build = (ROOT / "build.sh").read_text(encoding="utf-8")

        # report-only 觀察期尚未到 enforce，所以不應出現嚴格版（無 -Report-Only）
        self.assertIn("Content-Security-Policy-Report-Only", build)
        self.assertIn("Strict-Transport-Security", build)
        self.assertIn("X-Content-Type-Options: nosniff", build)
        self.assertIn("Referrer-Policy", build)
        self.assertIn("report-uri /__csp_report", build)
        self.assertIn("Report-To", build)

    def test_app_package_patch_includes_local_python_modules(self):
        patcher = load_app_package_patcher()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_dir = root / "flet_app"
            package = app_dir / "build" / "web" / "assets" / "app" / "app.zip"
            admin_dir = root / "admin"
            package.parent.mkdir(parents=True)
            app_dir.mkdir(exist_ok=True)
            admin_dir.mkdir()
            (app_dir / "main.py").write_text("import ui_theme\n", encoding="utf-8")
            (app_dir / "ui_theme.py").write_text("THEME = {}\n", encoding="utf-8")
            (app_dir / "plant_api.py").write_text("WORKER_URL = ''\n", encoding="utf-8")
            (admin_dir / "animals.json").write_text('{"animals": []}\n', encoding="utf-8")
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("main.py", "old")

            previous_root = patcher.ROOT
            previous_app_dir = patcher.APP_DIR
            try:
                patcher.ROOT = root
                patcher.APP_DIR = app_dir
                patched = patcher.rewrite_app_package(package)
            finally:
                patcher.ROOT = previous_root
                patcher.APP_DIR = previous_app_dir

            with zipfile.ZipFile(package) as archive:
                names = set(archive.namelist())
                self.assertIn("main.py", names)
                self.assertIn("ui_theme.py", names)
                self.assertIn("plant_api.py", names)
                self.assertNotIn("types.py", names)
                self.assertIn("admin/animals.json", names)
                self.assertEqual(archive.read("main.py").decode("utf-8").replace("\r\n", "\n"), "import ui_theme\n")
                self.assertEqual(len([name for name in archive.namelist() if name == "main.py"]), 1)
            self.assertIn("ui_theme.py", patched)

    def test_loader_patch_injects_preloads_for_versioned_runtime_assets(self):
        patcher = load_loader_patcher()
        previous_build_id = os.environ.get("FLET_BUILD_ID")
        os.environ["FLET_BUILD_ID"] = "unit-test-build"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                index = root / "index.html"
                app_dir = root / "assets" / "app"
                app_dir.mkdir(parents=True)
                (app_dir / "app.zip").write_bytes(b"fake app package")
                index.write_text(
                    "<html><head></head><body><script src=\"python.js\"></script></body></html>",
                    encoding="utf-8",
                )

                patcher.patch_index(index)

                html = index.read_text(encoding="utf-8")
                self.assertTrue((app_dir / "app-unit-test-build.zip").exists())
                self.assertIn('rel="preload" href="assets/app/app-unit-test-build.zip"', html)
                self.assertIn('rel="preload" href="pyodide/pyodide.js"', html)
                self.assertIn('rel="preload" href="canvaskit/canvaskit.js"', html)
                self.assertIn('flet.appPackageUrl = "assets/app/app-unit-test-build.zip"', html)
        finally:
            if previous_build_id is None:
                os.environ.pop("FLET_BUILD_ID", None)
            else:
                os.environ["FLET_BUILD_ID"] = previous_build_id


if __name__ == "__main__":
    unittest.main()
