import unittest

from app import decode_pokedex_cache, encode_pokedex_cache, normalize_pokedex, safe_text


class AppHelperTests(unittest.TestCase):
    def test_safe_text_escapes_html(self):
        self.assertEqual(safe_text('<script>alert("x")</script>'), "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;")

    def test_safe_text_uses_default_for_empty_values(self):
        self.assertEqual(safe_text(None), "N/A")
        self.assertEqual(safe_text(""), "N/A")

    def test_pokedex_cache_round_trips_collected_items(self):
        pokedex = {
            "榕樹": {
                "zh_name": "榕樹",
                "eng_name": "Chinese banyan",
                "sci_name": "Ficus microcarpa",
                "desc": "常見植物。",
                "type": "plant",
            }
        }

        encoded = encode_pokedex_cache(pokedex)
        restored = decode_pokedex_cache(encoded)

        self.assertEqual(restored, pokedex)

    def test_pokedex_cache_ignores_invalid_payloads(self):
        self.assertEqual(decode_pokedex_cache("not-valid-cache"), {})
        self.assertEqual(normalize_pokedex(["bad"]), {})

    def test_pokedex_cache_normalizes_untrusted_fields(self):
        restored = normalize_pokedex(
            {
                "測試": {
                    "zh_name": "測試",
                    "desc": "描述",
                    "unexpected": "<script>",
                    "nested": {"bad": True},
                }
            }
        )

        self.assertEqual(restored, {"測試": {"zh_name": "測試", "desc": "描述"}})


if __name__ == "__main__":
    unittest.main()
