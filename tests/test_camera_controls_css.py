from pathlib import Path
import unittest


STYLE_PATH = Path(__file__).resolve().parents[1] / "style.css"


class CameraControlsCssTests(unittest.TestCase):
    def test_camera_controls_have_visible_labels(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn('content: "前後鏡頭"', css)
        self.assertIn('content: "拍攝"', css)
        self.assertIn('content: "重拍"', css)

    def test_camera_buttons_keep_native_elements_accessible(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("[data-testid=\"stCameraInput\"] button * {\n    display: none", css)
        self.assertIn("clip: rect(0, 0, 0, 0)", css)


if __name__ == "__main__":
    unittest.main()
