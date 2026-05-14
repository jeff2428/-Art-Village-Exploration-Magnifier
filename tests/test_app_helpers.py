import unittest

from app import safe_text


class AppHelperTests(unittest.TestCase):
    def test_safe_text_escapes_html(self):
        self.assertEqual(safe_text('<script>alert("x")</script>'), "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;")

    def test_safe_text_uses_default_for_empty_values(self):
        self.assertEqual(safe_text(None), "N/A")
        self.assertEqual(safe_text(""), "N/A")


if __name__ == "__main__":
    unittest.main()
