from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


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
        self.assertNotIn("2b1004", worker)
        self.assertIn("github\\.io", worker)
        self.assertIn("pages\\.dev", worker)
        self.assertIn("ALLOWED_ORIGIN", worker)
        self.assertIn("Access-Control-Allow-Origin", worker)
        self.assertIn('name = "art-village-magnifier"', wrangler)
        self.assertIn('main = "index.js"', wrangler)

    def test_flet_app_has_magnifier_handle_callbacks(self):
        handle = (ROOT / "flet_app" / "magnifier_handle.py").read_text(encoding="utf-8")

        self.assertIn("class MagnifierHandle", handle)
        self.assertIn("on_switch", handle)
        self.assertIn("on_capture", handle)
        self.assertIn("RadialGradient", handle)

    def test_flet_main_uses_worker_and_camera(self):
        main = (ROOT / "flet_app" / "main.py").read_text(encoding="utf-8")

        self.assertIn("flet_camera", main)
        self.assertIn("run_app", main)
        self.assertIn("探險放大鏡啟動中", main)
        self.assertIn("探險放大鏡載入失敗", main)
        self.assertIn("啟動相機", main)
        self.assertIn("ft.RadioGroup", main)
        self.assertIn("WORKER_URL", main)
        self.assertIn("take_picture", main)
        self.assertIn("set_description", main)
        self.assertIn("GridView", main)
        self.assertIn("ft.run(main)", main)

    def test_cloudflare_pages_builds_and_patches_loader(self):
        build = (ROOT / "build.sh").read_text(encoding="utf-8")
        dev = (ROOT / "scripts" / "dev.ps1").read_text(encoding="utf-8")
        install_dev = (ROOT / "scripts" / "install-dev.ps1").read_text(encoding="utf-8")
        patcher = (ROOT / "scripts" / "patch_flet_loader.py").read_text(encoding="utf-8")
        wrangler = (ROOT / "wrangler.toml").read_text(encoding="utf-8")

        self.assertFalse((ROOT / ".github" / "workflows" / "deploy.yml").exists())
        self.assertIn("flet build web", build)
        self.assertIn("FLET_CLI_NO_RICH_OUTPUT", build)
        self.assertIn("--yes", build)
        self.assertIn("--route-url-strategy hash", build)
        self.assertIn("--web-renderer auto", build)
        self.assertIn("WORKER_URL", build)
        self.assertIn("patch_flet_loader.py", build)
        self.assertIn('pages_build_output_dir = "flet_app/build/web"', wrangler)
        self.assertIn("flet_app/build/web/index.html", patcher)
        self.assertIn("探險家載入中", patcher)
        self.assertIn("explorer-pulse", patcher)
        self.assertIn("hasFletContent", patcher)
        self.assertIn("flet run -d -w main.py", dev)
        self.assertIn("flet_app/requirements.txt", install_dev)


if __name__ == "__main__":
    unittest.main()
