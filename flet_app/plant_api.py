from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

import flet as ft

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]

try:
    import opencc

    _opencc_converter = opencc.OpenCC("s2t")

    def to_traditional_chinese(text: str) -> str:
        return _opencc_converter.convert(text)
except ImportError:
    def to_traditional_chinese(text: str) -> str:
        return text


LOW_CONFIDENCE_THRESHOLD = 50.0
PLANT_ORGAN_OPTIONS: dict[str, str] = {
    "auto": "自動",
    "leaf": "葉",
    "flower": "花",
    "fruit": "果",
    "bark": "樹皮",
}
PLANT_ORGAN_ICONS: dict[str, object] = {
    "auto": ft.Icons.AUTO_AWESOME,
    "leaf": ft.Icons.ECO,
    "flower": ft.Icons.LOCAL_FLORIST,
    "fruit": ft.Icons.SPA,
    "bark": ft.Icons.PARK,
}
MAX_CARD_IMAGE_DATA_URL_LENGTH = 180_000
MAX_POKEDEX_STORAGE_BYTES = 50_000_000
MAX_IMAGE_WIDTH = 800
IMAGE_COMPRESSION_QUALITY = 85

UNKNOWN_METADATA: dict[str, dict[str, str]] = {
    "toxicity": {"label": "資料待確認", "detail": "PlantNet 不提供毒性判斷，需查證可靠資料。"},
    "invasive": {"label": "資料待確認", "detail": "尚未建立此物種的在地外來種資料。"},
}
PLANT_METADATA: dict[str, dict[str, dict[str, str]]] = {
    "Ficus microcarpa": {
        "toxicity": {"label": "無明確毒性資料", "detail": "未作食用安全判斷，接觸後仍建議洗手。"},
        "invasive": {"label": "非外來種", "detail": "台灣常見榕屬樹種，實地仍以地方資料為準。"},
    },
    "Hibiscus rosa-sinensis": {
        "toxicity": {"label": "無明確毒性資料", "detail": "常見觀賞植物，仍不建議任意食用。"},
        "invasive": {"label": "資料待確認", "detail": "不同地區栽培與逸出狀態不同。"},
    },
}

try:
    from build_config import WORKER_URL
except ImportError:
    WORKER_URL = "https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev"


def common_names_by_script(species: dict[str, Any]) -> tuple[list[str], list[str]]:
    chinese_names: list[str] = []
    other_names: list[str] = []
    for raw_name in species.get("commonNames", []) or []:
        name = str(raw_name).strip()
        if not name:
            continue
        has_cjk = any("\u4e00" <= char <= "\u9fff" for char in name)
        if has_cjk:
            chinese_names.append(to_traditional_chinese(name))
        else:
            other_names.append(name)
    return chinese_names, other_names


def first_common_name(species: dict[str, Any], chinese: bool) -> str | None:
    chinese_names, other_names = common_names_by_script(species)
    names = chinese_names if chinese else other_names
    return names[0] if names else None


def metadata_for_scientific_name(scientific: str) -> dict[str, dict[str, str]]:
    metadata = PLANT_METADATA.get(scientific, UNKNOWN_METADATA)
    return {
        "toxicity": dict(metadata["toxicity"]),
        "invasive": dict(metadata["invasive"]),
    }


def bool_label(value: Any, true_label: str, false_label: str, unknown_label: str = "資料待確認") -> str:
    if value is True:
        return true_label
    if value is False:
        return false_label
    return unknown_label


def metadata_from_perenual(perenual: dict[str, Any], fallback: dict[str, dict[str, str]]) -> dict[str, Any]:
    if perenual.get("status") not in ("ok", "cached"):
        return {
            "toxicity": dict(fallback["toxicity"]),
            "invasive": dict(fallback["invasive"]),
            "care": {},
            "source": "PlantNet",
        }

    poisonous_to_humans = perenual.get("poisonous_to_humans")
    poisonous_to_pets = perenual.get("poisonous_to_pets")
    invasive = perenual.get("invasive")
    toxicity_detail = "Perenual 二次查詢資料。"
    if poisonous_to_pets is True:
        toxicity_detail += " 另標示可能對寵物有毒。"
    elif poisonous_to_pets is False:
        toxicity_detail += " 另標示未列為寵物有毒。"

    return {
        "toxicity": {
            "label": bool_label(poisonous_to_humans, "有毒", "未列為有毒"),
            "detail": toxicity_detail,
        },
        "invasive": {
            "label": bool_label(invasive, "可能具侵略性", "未列為侵略性"),
            "detail": "Perenual 物種資料，仍建議以在地資料確認。",
        },
        "care": {
            "澆水": perenual.get("watering") or "",
            "日照": "、".join(perenual.get("sunlight") or []),
            "生命週期": perenual.get("cycle") or "",
            "照護難度": perenual.get("care_level") or "",
        },
        "source": "Perenual",
    }


def plant_candidate_from_result(result: dict[str, Any], perenual: dict[str, Any] | None = None) -> dict[str, Any]:
    species = result.get("species") or {}
    scientific = species.get("scientificNameWithoutAuthor") or species.get("scientificName") or "Unknown"
    chinese_names, other_names = common_names_by_script(species)
    zh_name = chinese_names[0] if chinese_names else scientific
    aliases = [name for name in chinese_names[1:] if name != zh_name]
    eng_name = other_names[0] if other_names else "N/A"
    score = float(result.get("score") or 0)
    confidence = round(score * 100, 1)
    metadata = metadata_for_scientific_name(scientific)
    enriched_metadata = metadata_from_perenual(perenual or {}, metadata)
    perenual_description = (perenual or {}).get("description") if (perenual or {}).get("status") in ("ok", "cached") else ""
    description = perenual_description or f"PlantNet 推測為 {zh_name}（{scientific}）。"

    return {
        "zh_name": zh_name,
        "aliases": aliases,
        "eng_name": eng_name,
        "sci_name": scientific,
        "emoji": "🌿",
        "type": "plant",
        "desc": description,
        "confidence": confidence,
        "is_low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
        "toxicity": enriched_metadata["toxicity"],
        "invasive": enriched_metadata["invasive"],
        "care": enriched_metadata["care"],
        "metadata_source": enriched_metadata["source"],
        "metadata_status": (perenual or {}).get("status", "not_requested"),
    }


def parse_plantnet_result(payload: dict[str, Any]) -> dict[str, Any] | None:
    results = payload.get("results") or []
    if not results:
        return None

    candidates = [
        plant_candidate_from_result(result or {}, payload.get("perenual") if index == 0 else None)
        for index, result in enumerate(results[:4])
    ]
    primary = candidates[0]
    primary["alternatives"] = candidates[1:]
    primary["needs_confirmation"] = primary["is_low_confidence"]
    return primary


def confidence_text(item: dict[str, Any]) -> str:
    confidence = item.get("confidence", 0)
    if not confidence:
        return ""
    suffix = "，建議確認" if item.get("is_low_confidence") else ""
    return f"信心度 {confidence}%{suffix}"


def card_image_from_capture(capture: Any, max_data_url_length: int = MAX_CARD_IMAGE_DATA_URL_LENGTH) -> dict[str, str]:
    try:
        if isinstance(capture, str) and capture.startswith("data:") and len(capture) <= max_data_url_length:
            return {"src": capture, "label": "拍攝照片"}
        binary, mime = capture_to_bytes(capture)
        if "image" in mime:
            binary = compress_image(binary, mime)
        data_url = f"data:image/jpeg;base64,{base64.b64encode(binary).decode('ascii')}"
        if len(data_url) <= max_data_url_length:
            return {"src": data_url, "label": "拍攝照片"}
    except Exception:
        pass
    return {"src": "", "label": "照片過大，未存入圖鑑"}


def capture_to_bytes(capture: Any) -> tuple[bytes, str]:
    if isinstance(capture, bytes):
        return capture, "image/jpeg"
    if isinstance(capture, bytearray):
        return bytes(capture), "image/jpeg"
    if isinstance(capture, memoryview):
        return capture.tobytes(), "image/jpeg"
    if isinstance(capture, str) and capture.startswith("data:"):
        header, encoded = capture.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
        return base64.b64decode(encoded), mime
    if isinstance(capture, str):
        image_path = Path(capture)
        if image_path.exists():
            mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
            return image_path.read_bytes(), mime
        return base64.b64decode(capture), "image/jpeg"
    raise TypeError("相機回傳了無法辨識的圖片格式")


def compress_image(binary: bytes, mime: str) -> bytes:
    if Image is None:
        return binary
    try:
        image = Image.open(BytesIO(binary))
        if image.width > MAX_IMAGE_WIDTH:
            ratio = MAX_IMAGE_WIDTH / image.width
            new_height = int(image.height * ratio)
            image = image.resize((MAX_IMAGE_WIDTH, new_height), Image.LANCZOS)
        buffer = BytesIO()
        fmt = "WEBP" if hasattr(Image, "registered_extensions") and ".webp" in Image.registered_extensions() else "JPEG"
        image.save(buffer, format=fmt, quality=IMAGE_COMPRESSION_QUALITY, optimize=True)
        return buffer.getvalue()
    except Exception:
        return binary


class RecognitionServiceError(RuntimeError):
    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


def post_image_to_worker_sync(binary: bytes, mime: str, organ: str = "leaf") -> dict[str, Any]:
    import requests

    response = requests.post(
        WORKER_URL,
        files={"images": ("capture.jpg", binary, mime)},
        data={"organs": organ},
        timeout=30,
    )
    if not response.ok:
        raise RecognitionServiceError(worker_error_message(response.status_code, response.text))
    return response.json()


def worker_error_message(status_code: int, text: str) -> str:
    snippet = " ".join((text or "").strip().split())[:120]
    if status_code == 404 and "1042" in snippet:
        return "辨識服務尚未部署，請檢查 Worker 網址"
    if status_code in (400, 404):
        return "沒有辨識到植物，請對準葉子、花或果實再拍一次"
    if status_code == 405:
        return "辨識服務方法錯誤，請稍後再試"
    if status_code in (401, 403):
        return "辨識服務金鑰未通過，請檢查 Worker 的 PLANTNET_API_KEY"
    if status_code == 413:
        return "照片太大，請靠近植物後再拍一次"
    if status_code == 426:
        return "前端版本過舊，請稍後再拍一次"
    if status_code == 429:
        return "辨識服務忙碌，請稍後再試"
    if 500 <= status_code < 600:
        return "辨識服務暫時忙碌，請稍後再試"
    return f"辨識服務暫時無法處理（{status_code}）"


def metadata_url_for_scientific_name(scientific_name: str) -> str:
    return f"{WORKER_URL.rstrip('/')}/metadata?scientificName={quote(scientific_name)}"


def get_metadata_from_worker_sync(scientific_name: str) -> dict[str, Any]:
    import requests

    response = requests.get(metadata_url_for_scientific_name(scientific_name), timeout=20)
    if not response.ok:
        raise RecognitionServiceError(worker_error_message(response.status_code, response.text))
    return response.json()


async def get_metadata_from_worker(scientific_name: str) -> dict[str, Any]:
    if "YOUR-WORKER" in WORKER_URL:
        raise RuntimeError("尚未設定 Cloudflare Pages 的 WORKER_URL")

    try:
        from js import fetch  # type: ignore

        response = await fetch(metadata_url_for_scientific_name(scientific_name))
        text = await response.text()
        if not response.ok:
            raise RecognitionServiceError(worker_error_message(response.status, text))
        return json.loads(text)
    except ModuleNotFoundError:
        return await asyncio.to_thread(get_metadata_from_worker_sync, scientific_name)


async def post_image_to_worker(capture: Any, organ: str = "leaf") -> dict[str, Any]:
    if "YOUR-WORKER" in WORKER_URL:
        raise RuntimeError("尚未設定 Cloudflare Pages 的 WORKER_URL")

    binary, mime = capture_to_bytes(capture)

    try:
        from js import Blob, FormData, Object, Uint8Array, fetch  # type: ignore
        from pyodide.ffi import to_js  # type: ignore

        image_array = Uint8Array.new(to_js(list(binary)))
        blob = Blob.new([image_array], {"type": mime})

        form = FormData.new()
        form.append("organs", organ)
        form.append("images", blob, "capture.jpg")

        fetch_options = to_js({"method": "POST", "body": form}, dict_converter=Object.fromEntries)
        response = await fetch(WORKER_URL, fetch_options)
        text = await response.text()
        if not response.ok:
            raise RecognitionServiceError(worker_error_message(response.status, text))
        return json.loads(text)
    except ModuleNotFoundError:
        return await asyncio.to_thread(post_image_to_worker_sync, binary, mime, organ)
