from pathlib import Path
import unittest


STYLE_PATH = Path(__file__).resolve().parents[1] / "style.css"


class CameraControlsCssTests(unittest.TestCase):
    def test_camera_controls_have_visible_labels(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn('content: "前後鏡頭"', css)
        self.assertIn('content: "無法切換"', css)
        self.assertIn('content: "拍攝"', css)
        self.assertIn('content: "重拍"', css)

    def test_camera_buttons_keep_native_elements_accessible(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("[data-testid=\"stCameraInput\"] button * {\n    display: none", css)
        self.assertIn("clip: rect(0, 0, 0, 0)", css)

    def test_camera_buttons_are_stacked_on_magnifier_handle(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn("height: clamp(224px, 58vw, 260px)", css)
        self.assertIn("[data-testid=\"stCameraInputSwitchButton\"]", css)
        self.assertIn("top: calc(min(76vw, 320px) + clamp(22px, 6vw, 30px))", css)
        self.assertIn("[data-testid=\"stCameraInput\"] [data-testid=\"stCameraInputButton\"]", css)
        self.assertIn("top: calc(min(76vw, 320px) + clamp(104px, 28vw, 126px))", css)
        self.assertIn("left: 50%", css)

    def test_disabled_switch_button_shows_unavailable_state(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertIn("[data-testid=\"stCameraInputSwitchButton\"] button:disabled::before", css)
        self.assertIn("[data-testid=\"stCameraInputSwitchButton\"] button[aria-disabled=\"true\"]::before", css)
        self.assertIn("[data-testid=\"stCameraInput\"]:not(:has([data-testid=\"stCameraInputSwitchButton\"]))::before", css)
        self.assertIn("cursor: not-allowed", css)

    def test_capture_button_is_not_used_as_switch_button(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertNotIn("[data-testid=\"stCameraInput\"] > div button::before", css)
        self.assertNotIn("[data-testid=\"stCameraInput\"] > div button", css)

    def test_mobile_switch_wrapper_position_is_not_reset(self):
        css = STYLE_PATH.read_text(encoding="utf-8")

        self.assertNotIn('[data-testid="stCameraInput"] div {\n    position: static', css)
        self.assertIn('[data-testid="stCameraInputWebcamComponent"]', css)
        self.assertIn('[data-testid="stCameraInputWebcamStyledBox"]', css)


if __name__ == "__main__":
    unittest.main()
