"""External API integration for plant identification."""

import logging
from pathlib import PurePath
from urllib.parse import quote

import requests
from config import ALLOWED_IMAGE_TYPES, MAX_UPLOAD_BYTES, PLANTNET_API_KEY, REQUEST_TIMEOUT_SECONDS

try:
    from opencc import OpenCC
except ImportError:
    OpenCC = None


LOGGER = logging.getLogger(__name__)


class _IdentityConverter:
    def convert(self, text):
        return text


CC_CONVERTER = OpenCC("s2t") if OpenCC else _IdentityConverter()
PLANTNET_IDENTIFY_URL = "https://my-api.plantnet.org/v2/identify/all"
WIKIPEDIA_SUMMARY_URL = "https://zh.wikipedia.org/api/rest_v1/page/summary/{title}"
GENERIC_CONNECTION_ERROR = "連線異常，請稍後再試。"


def _error(message):
    return {"success": False, "error": message}


def _safe_filename(name):
    filename = PurePath(name or "upload.jpg").name
    return filename.replace("\r", "").replace("\n", "") or "upload.jpg"


def _validate_image_file(image_file):
    content_type = getattr(image_file, "type", "")
    if content_type not in ALLOWED_IMAGE_TYPES:
        return None, _error("圖片格式不支援，請使用 JPG、PNG 或 WebP。")

    image_bytes = image_file.getvalue()
    if not image_bytes:
        return None, _error("沒有收到圖片內容，請重新拍攝。")
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        return None, _error("圖片太大，請使用 5MB 以下的圖片。")

    return image_bytes, None


def _extract_best_match(result):
    matches = result.get("results") or []
    if not matches:
        return None
    species = matches[0].get("species") or {}
    sci_name = species.get("scientificNameWithoutAuthor")
    if not sci_name:
        return None
    return species


def _fetch_wikipedia_summary(zh_name):
    description = "這是一株神秘的植物，百科中暫時找不到詳細故事。"
    try:
        wiki_res = requests.get(
            WIKIPEDIA_SUMMARY_URL.format(title=quote(zh_name, safe="")),
            params={"redirect": "true"},
            headers={"Accept-Language": "zh-tw"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if wiki_res.status_code == 200:
            return CC_CONVERTER.convert(wiki_res.json().get("extract", description))
    except (requests.RequestException, ValueError):
        LOGGER.info("Wikipedia summary lookup failed")
    return description

def identify_plant_from_api(image_file):
    """
    負責呼叫 PlantNet API 與 Wikipedia API 進行植物辨識與資料擷取。
    """
    if not PLANTNET_API_KEY:
        return _error("尚未設定 PlantNet API 金鑰。請在 Streamlit secrets 或 PLANTNET_API_KEY 環境變數中設定。")

    image_bytes, validation_error = _validate_image_file(image_file)
    if validation_error:
        return validation_error

    files = [("images", (_safe_filename(getattr(image_file, "name", "")), image_bytes, image_file.type))]
    
    try:
        response = requests.post(
            PLANTNET_IDENTIFY_URL,
            params={"api-key": PLANTNET_API_KEY, "lang": "zh"},
            files=files,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            return _error("辨識失敗，請確認圖片清晰度或網路狀態。")

        result = response.json()
        species = _extract_best_match(result)
        if not species:
            return _error("找不到匹配的植物。")

        sci_name = species["scientificNameWithoutAuthor"]
        common_names = species.get("commonNames", [])
        
        eng_name = next((n for n in common_names if n.replace(" ","").isascii()), "N/A")
        raw_zh_name = next((n for n in common_names if any('\u4e00' <= c <= '\u9fff' for c in n)), sci_name)
        zh_name = CC_CONVERTER.convert(raw_zh_name)

        return {
            "success": True,
            "sci_name": sci_name,
            "eng_name": eng_name,
            "zh_name": zh_name,
            "desc": _fetch_wikipedia_summary(zh_name),
            "type": "plant"
        }
    except (requests.RequestException, ValueError):
        LOGGER.info("Plant identification request failed")
        return _error(GENERIC_CONNECTION_ERROR)
