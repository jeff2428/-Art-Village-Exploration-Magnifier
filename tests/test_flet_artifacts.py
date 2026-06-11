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

    def test_frontend_load_optimization_keeps_heavy_opencc_out_of_pyodide(self):
        requirements = (ROOT / "flet_app" / "requirements.txt").read_text(encoding="utf-8").lower()
        plant_api = (ROOT / "flet_app" / "plant_api.py").read_text(encoding="utf-8")
        worker = (ROOT / "worker" / "index.js").read_text(encoding="utf-8")

        self.assertNotIn("opencc", requirements)
        self.assertNotIn("import opencc", plant_api)
        self.assertIn("function s2t", worker)
        self.assertIn("commonNames = result.species.commonNames.map(s2t)", worker)
        self.assertTrue((ROOT / "scripts" / "measure_flet_payload.py").exists())

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
        camera_mgr = (ROOT / "flet_app" / "services" / "camera_manager.py").read_text(encoding="utf-8")
        cm = (ROOT / "flet_app" / "camera_utils.py").read_text(encoding="utf-8")
        welcome = (ROOT / "flet_app" / "views" / "welcome.py").read_text(encoding="utf-8")
        plant_api = (ROOT / "flet_app" / "plant_api.py").read_text(encoding="utf-8")
        pokedex_manager = (ROOT / "flet_app" / "pokedex_manager.py").read_text(encoding="utf-8")
        storage = (ROOT / "flet_app" / "services" / "storage.py").read_text(encoding="utf-8")
        recognition = (ROOT / "flet_app" / "services" / "recognition.py").read_text(encoding="utf-8")
        dialogs = (ROOT / "flet_app" / "views" / "dialogs.py").read_text(encoding="utf-8")
        plant_view = (ROOT / "flet_app" / "views" / "plant_view.py").read_text(encoding="utf-8")

        self.assertIn("flet_camera", main)
        self.assertIn("run_app", main)
        self.assertIn("\\u63a2\\u96aa\\u653e\\u5927\\u93e1\\u8f09\\u5165\\u5931\\u6557", main)
        self.assertIn("\\u91cd\\u65b0\\u555f\\u52d5\\u76f8\\u6a5f", main)
        self.assertIn("camera_initializing", camera_mgr)
        self.assertIn("asyncio.wait_for(self._state.camera.get_available_cameras(", camera_mgr)
        self.assertIn("asyncio.wait_for(", camera_mgr)
        self.assertIn("select_preferred_cameras", camera_mgr)
        self.assertIn("on_switch=self.switch_camera", camera_mgr)
        self.assertIn("on_capture=self.capture_and_identify", camera_mgr)
        self.assertNotIn("on_scale_start=on_pinch_start", main)
        self.assertNotIn("on_scale_update=on_pinch_update", main)
        self.assertIn("MIN_CAMERA_ZOOM", camera_mgr)
        self.assertIn("MAX_CAMERA_ZOOM", camera_mgr)
        self.assertIn("clamp_camera_zoom", camera_mgr)
        self.assertIn("create_background_task(save_cached_pokedex_debounced(self.state.pokedex))", storage)
        self.assertIn("mark_load_timing", main)
        self.assertIn("art-village:camera-ready", camera_mgr)
        self.assertIn("AppMode", main)
        self.assertIn("GalleryService", main)
        self.assertIn("CameraManager", main)
        self.assertIn("RecognitionService", main)
        self.assertIn("build_gallery_panel", main)
        self.assertIn("show_gallery_card", main)
        self.assertIn("正在呼喚小夥伴們", welcome)
        self.assertIn("LENS_VIEWPORT_SIZE", camera_mgr)
        self.assertIn("CAMERA_PREVIEW_SIZE = 420", cm)
        self.assertIn("CAMERA_PREVIEW_OFFSET = -58", cm)
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
        self.assertIn("UNKNOWN_METADATA", plant_api)
        self.assertIn("metadata_for_scientific_name", plant_api)
        self.assertIn("metadata_from_perenual", plant_api)
        self.assertIn("metadata_url_for_scientific_name", plant_api)
        self.assertIn("get_metadata_from_worker", plant_api)
        self.assertIn("refresh_plant_metadata", recognition)
        self.assertIn('plant.get("metadata_status") == "pending"', main)
        self.assertIn("worker_timing", camera_mgr)
        self.assertIn("art-village:identify-start", camera_mgr)
        self.assertIn("art-village:identify-primary-ready", camera_mgr)
        self.assertIn("payload.get(\"perenual\")", plant_api)
        self.assertIn("card_image_from_capture", camera_mgr)
        self.assertIn("organ_mode = ft.SegmentedButton", main)
        self.assertIn('selected=["auto"]', main)
        self.assertIn("PLANT_ORGAN_ICONS", main)
        self.assertIn("ft.Segment", main)
        self.assertIn("selected_organ_value", main)
        self.assertIn("organ_selector", plant_view)
        self.assertIn("scrollable=True", dialogs)
        self.assertIn("dialog_content_height", dialogs)
        self.assertIn("page.scroll = ft.ScrollMode.AUTO", main)
        self.assertIn("captured_image", dialogs)
        self.assertIn("ft.BoxFit.COVER", dialogs)
        self.assertNotIn("ft.ImageFit", main)
        self.assertIn("ft.Padding.symmetric", dialogs)
        self.assertNotIn("ft.padding.symmetric", main)
        self.assertIn("aliases", dialogs)
        self.assertIn("toxicity", dialogs)
        self.assertIn("invasive", dialogs)
        self.assertIn("尚無拍攝照片", dialogs)
        self.assertIn("await post_image_to_worker(image_data, selected_organ)", camera_mgr)
        self.assertIn("show_recognition_loading_card()", recognition)
        self.assertIn("close_recognition_loading_card(update_page=False)", recognition)
        self.assertIn("辨識中", dialogs)
        self.assertIn("show_plant_card(plant[\"zh_name\"], plant)", recognition)
        self.assertIn("alternatives", dialogs)
        self.assertIn("建議確認", plant_api)
        self.assertIn("clear_legacy_snapshot_cache", main)
        self.assertNotIn("make_snapshot", main)
        self.assertNotIn("snapshot_to_capture", main)
        self.assertNotIn("retry_pending_snapshots", main)
        self.assertNotIn("離線暫存快照", main)
        self.assertNotIn("重送暫存快照", main)
        self.assertIn("ProgressRing", main)
        self.assertNotIn("藝素村手繪探險圖鑑", main)
        self.assertNotIn('section_label("🔍", "探險鏡頭")', main)
        self.assertIn("selected_mode", main)
        self.assertNotIn("ft.RadioGroup", main)
        self.assertIn("WORKER_URL", plant_api)
        self.assertIn("尚未設定 Cloudflare Pages 的 WORKER_URL", plant_api)
        self.assertIn("worker_error_message", plant_api)
        self.assertIn("Object.fromEntries", plant_api)
        self.assertIn("mark_explorer_ready", main)
        self.assertIn("__artVillageReady", main)
        self.assertIn("辨識服務尚未部署", plant_api)
        self.assertIn("PLANTNET_API_KEY", plant_api)
        self.assertIn("requests.post", plant_api)
        self.assertIn("ft.run(main)", main)
        self.assertIn("FLET_SKIP_RUN", main)
        self.assertNotIn('__name__ == "__main__"', main)
        self.assertNotIn("text=f", main)
        self.assertIn("show_animal_card", main)
        self.assertIn("page.show_dialog", dialogs)
        self.assertIn("build_mode_selector", main)
        self.assertIn("ft.TextButton", main)
        self.assertIn('selected_mode["value"] == "animal"', main)
        self.assertNotIn("ft.margin.only", main)
        self.assertNotIn("WARNING_AMBIGUOUS", main)
        self.assertIn("welcome_screen", main)
        self.assertIn("start_exploration", main)
        self.assertIn("report_performance", main)
        self.assertIn("welcome_screen.visible = False", main)
        add_pos = main.index("page.add(welcome_screen, shell)")
        ready_pos = main.index("mark_explorer_ready()", add_pos)
        start_pos = main.index("async def start_exploration")
        click_pos = main.index("build_start_button(on_click=on_start_click)")
        self.assertGreater(ready_pos, add_pos)
        self.assertGreater(add_pos, start_pos)
        self.assertGreater(add_pos, click_pos)
        self.assertIn("camera.apply_theme_colors()", main)
        self.assertIn("if value == \"plant\":\n            create_background_task(camera.initialize())", main)
        self.assertNotIn("await restore_camera_preview()", main)

    def test_browser_only_js_imports_have_local_fallbacks(self):
        pokedex_manager = (ROOT / "flet_app" / "pokedex_manager.py").read_text(encoding="utf-8")
        plant_api = (ROOT / "flet_app" / "plant_api.py").read_text(encoding="utf-8")

        self.assertIn("except (ImportError, json.JSONDecodeError, AttributeError):", pokedex_manager)
        self.assertIn("except (ImportError, AttributeError, TypeError):", pokedex_manager)
        self.assertIn("except (ImportError, ModuleNotFoundError):", plant_api)
        self.assertTrue((ROOT / "flet_app" / "js.py").exists())
        package_patcher = (ROOT / "scripts" / "patch_flet_app_package.py").read_text(encoding="utf-8")
        self.assertIn('path.name != "js.py"', package_patcher)

    def test_animal_view_is_customer_facing_without_admin_entry(self):
        animal_view = (ROOT / "flet_app" / "views" / "animal_view.py").read_text(encoding="utf-8")

        self.assertIn("get_animals_view", animal_view)
        self.assertIn("on_animal_click", animal_view)
        self.assertIn("ft.TextButton", animal_view)
        self.assertIn("on_click=open_card", animal_view)
        self.assertIn("點擊查看介紹", animal_view)
        self.assertIn("目前尚無動物介紹", animal_view)
        self.assertNotIn("admin/animals.html", animal_view)
        self.assertNotIn("動物管理", animal_view)
        self.assertNotIn("後台", animal_view)
        self.assertNotIn("launch_url", animal_view)

    def test_animal_admin_page_requires_simple_password_gate(self):
        admin_page = (ROOT / "admin" / "animals.html").read_text(encoding="utf-8")

        self.assertIn("ADMIN_PASSWORD", admin_page)
        self.assertIn("預設管理密碼：<strong>artvillage</strong>", admin_page)
        self.assertIn("input.value.trim() === ADMIN_PASSWORD", admin_page)
        self.assertIn("artVillageAnimalAdminAuthed", admin_page)
        self.assertIn("sessionStorage", admin_page)
        self.assertIn("authShell", admin_page)
        self.assertIn("appShell", admin_page)
        self.assertIn("artVillageAnimals", admin_page)
        self.assertIn("ANIMALS_WORKER_URL", admin_page)
        self.assertIn("saveAnimalsToWorker", admin_page)
        self.assertIn("fetch(`${ANIMALS_WORKER_URL}/animals`", admin_page)
        self.assertIn("X-Admin-Password", admin_page)
        self.assertIn("artVillageAnimalSyncPassword", admin_page)
        self.assertIn("prompt('請輸入雲端同步密碼')", admin_page)
        self.assertNotIn("'X-Admin-Password': ADMIN_PASSWORD", admin_page)
        self.assertIn("downloadJSON", admin_page)
        self.assertIn("importJSONData", admin_page)
        self.assertIn("同瀏覽器前台會讀取本機草稿", admin_page)
        self.assertNotIn("localStorage.removeItem('artVillageAnimals')", admin_page)
        self.assertIn("PORTRAIT_MAX_WIDTH = 520", admin_page)
        self.assertIn("PHOTO_MAX_WIDTH = 760", admin_page)
        self.assertIn("MAX_PHOTOS_PER_ANIMAL = 4", admin_page)
        self.assertIn("QuotaExceededError", admin_page)
        self.assertIn("if (!saveToStorage())", admin_page)

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
        self.assertIn("ANIMALS_WORKER_URL", patcher)
        self.assertIn("prefetchAnimals", patcher)
        self.assertIn("artVillageAnimalsRemoteSyncedAt", patcher)
        self.assertIn("generate_service_worker", patcher)
        self.assertIn("sw.js", patcher)
        self.assertIn("fetch(event.request, {{ cache: 'reload' }})", patcher)
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

    def test_camera_zoom_uses_granular_updates_only(self):
        cm = (ROOT / "flet_app" / "services" / "camera_manager.py").read_text(encoding="utf-8")
        lines = cm.splitlines()
        func_start = next(i for i, line in enumerate(lines) if "def adjust_zoom" in line)
        next_def = next((i for i in range(func_start + 1, len(lines)) if lines[i].startswith("    def ")), len(lines))
        body = "\n".join(lines[func_start:next_def])
        self.assertNotIn("page.update()", body, "adjust_zoom 仍呼叫 page.update()")
        self.assertIn("_status_text.update()", body)
        self.assertIn("handle_slot.update()", body)

    def test_refresh_gallery_uses_grid_update_and_staggered_animation(self):
        st = (ROOT / "flet_app" / "services" / "storage.py").read_text(encoding="utf-8")
        lines = st.splitlines()
        func_start = next(i for i, line in enumerate(lines) if "def refresh" in line)
        next_def = next((i for i in range(func_start + 1, len(lines)) if lines[i].startswith("    def ")), len(lines))
        body = "\n".join(lines[func_start:next_def])
        self.assertIn("animate_opacity", body)
        self.assertIn("animate_offset", body)
        self.assertIn("self.grid.update()", body)

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
            (app_dir / "js.py").write_text("window = object()\n", encoding="utf-8")
            (app_dir / "views").mkdir()
            (app_dir / "views" / "welcome.py").write_text("WELCOME = True\n", encoding="utf-8")
            (admin_dir / "animals.json").write_text('{"animals": []}\n', encoding="utf-8")
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("main.py", "old")
                archive.writestr("js.py", "old")
                archive.writestr("views/welcome.py", "old")

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
                self.assertNotIn("js.py", names)
                self.assertIn("views/welcome.py", names)
                self.assertNotIn("types.py", names)
                self.assertIn("admin/animals.json", names)
                self.assertEqual(archive.read("main.py").decode("utf-8").replace("\r\n", "\n"), "import ui_theme\n")
                self.assertEqual(archive.read("views/welcome.py").decode("utf-8").replace("\r\n", "\n"), "WELCOME = True\n")
                self.assertEqual(len([name for name in archive.namelist() if name == "main.py"]), 1)
            self.assertTrue(package.with_name("app.zip.hash").exists())
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

    def test_loader_patch_refreshes_existing_cache_buster(self):
        patcher = load_loader_patcher()
        previous_build_id = os.environ.get("FLET_BUILD_ID")
        os.environ["FLET_BUILD_ID"] = "new-build"
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                index = root / "index.html"
                app_dir = root / "assets" / "app"
                app_dir.mkdir(parents=True)
                (app_dir / "app.zip").write_bytes(b"updated app package")
                index.write_text(
                    """<html><head>
<link rel="preload" href="assets/app/app-old-build.zip" as="fetch" crossorigin>
<script id="flet-cache-buster">
  flet.appPackageUrl = "assets/app/app-old-build.zip";
  flet.pyodideUrl = `${flet.pyodideUrl}?v=old-build`;
</script>
  <script src="python.js"></script></head><body>
<div id="explorer-loader"></div>
<script>
  const artVillageBuildId = "old-build";
</script>
</body></html>""",
                    encoding="utf-8",
                )

                patcher.patch_index(index)

                html = index.read_text(encoding="utf-8")
                self.assertTrue((app_dir / "app-new-build.zip").exists())
                self.assertIn('rel="preload" href="assets/app/app-new-build.zip"', html)
                self.assertIn('flet.appPackageUrl = "assets/app/app-new-build.zip"', html)
                self.assertIn("v=new-build", html)
                self.assertIn('const artVillageBuildId = "new-build";', html)
                self.assertNotIn("app-old-build.zip", html)
        finally:
            if previous_build_id is None:
                os.environ.pop("FLET_BUILD_ID", None)
            else:
                os.environ["FLET_BUILD_ID"] = previous_build_id


if __name__ == "__main__":
    unittest.main()
