from pathlib import Path
import unittest


STYLE_PATH = Path(__file__).resolve().parents[1] / "style.css"


class GalleryLayoutCssTests(unittest.TestCase):
    def test_gallery_panel_has_mobile_safe_spacing(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn(".st-key-gallery_panel", css)
        self.assertIn("env(safe-area-inset-bottom", css)
        self.assertIn("padding-bottom: calc(8.75rem + env(safe-area-inset-bottom, 0px))", css)

    def test_gallery_buttons_are_dense_mobile_grid(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn(".st-key-gallery_panel [data-testid=\"stHorizontalBlock\"]", css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", css)
        self.assertIn("[class*=\"st-key-gallery_\"] div.stButton > button", css)
        self.assertIn("overflow-wrap: anywhere", css)

    def test_gallery_uses_custom_summary_progress(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn(".gallery-summary", css)
        self.assertIn(".gallery-progress", css)
        self.assertIn(".gallery-progress span", css)


if __name__ == "__main__":
    unittest.main()
