import importlib
import os
import unittest
from unittest.mock import Mock, patch


class UploadedImage:
    name = "leaf.jpg"
    type = "image/jpeg"

    def __init__(self, content=b"image-bytes"):
        self._content = content

    def getvalue(self):
        return self._content


class ApiHandlerTests(unittest.TestCase):
    def setUp(self):
        os.environ["PLANTNET_API_KEY"] = "test-key"
        import config
        import api_handler

        importlib.reload(config)
        self.api_handler = importlib.reload(api_handler)

    def tearDown(self):
        os.environ.pop("PLANTNET_API_KEY", None)

    def test_rejects_unsupported_upload_type(self):
        upload = UploadedImage()
        upload.type = "text/html"

        result = self.api_handler.identify_plant_from_api(upload)

        self.assertFalse(result["success"])
        self.assertIn("格式不支援", result["error"])

    def test_missing_api_key_returns_safe_error(self):
        os.environ.pop("PLANTNET_API_KEY", None)
        import config

        importlib.reload(config)
        self.api_handler = importlib.reload(self.api_handler)

        result = self.api_handler.identify_plant_from_api(UploadedImage())

        self.assertFalse(result["success"])
        self.assertIn("尚未設定", result["error"])

    @patch("api_handler.requests.get")
    @patch("api_handler.requests.post")
    def test_identifies_plant_with_timeout_and_query_params(self, post, get):
        post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "results": [
                    {
                        "species": {
                            "scientificNameWithoutAuthor": "Ficus microcarpa",
                            "commonNames": ["榕樹", "Chinese banyan"],
                        }
                    }
                ]
            },
        )
        get.return_value = Mock(status_code=200, json=lambda: {"extract": "常見的行道樹。"})

        result = self.api_handler.identify_plant_from_api(UploadedImage())

        self.assertTrue(result["success"])
        self.assertEqual(result["zh_name"], "榕樹")
        self.assertEqual(result["eng_name"], "Chinese banyan")
        self.assertEqual(result["desc"], "常見的行道樹。")
        self.assertEqual(post.call_args.kwargs["params"]["api-key"], "test-key")
        self.assertIn("timeout", post.call_args.kwargs)
        self.assertIn("timeout", get.call_args.kwargs)

    @patch("api_handler.requests.post")
    def test_request_exception_does_not_leak_internal_details(self, post):
        post.side_effect = self.api_handler.requests.RequestException("token=secret")

        result = self.api_handler.identify_plant_from_api(UploadedImage())

        self.assertFalse(result["success"])
        self.assertNotIn("secret", result["error"])


if __name__ == "__main__":
    unittest.main()
